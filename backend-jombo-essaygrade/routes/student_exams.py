# routes/student_exams.py
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from auth_utils import require_student, validate_csrf
import models

router = APIRouter()

BLANTYRE = ZoneInfo("Africa/Blantyre")


def fmt_date(dt):
    if not dt: return None
    if hasattr(dt, 'year') and dt.year < 2000: return None
    if isinstance(dt, str): return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class AnswerSchema(BaseModel):
    question_id:     int
    selected_option: Optional[str] = None   # "A" | "B" | "C" | "D"  — MCQ only
    answer_text:     Optional[str] = None   # structured only


class SubmitExamRequest(BaseModel):
    exam_id:    int
    answers:    List[AnswerSchema]
    csrf_token: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/student/exams
#  Returns all active exams for classes the student is enrolled in,
#  with the student's own submission attached (if any).
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/exams")
def get_student_exams(ctx: dict = Depends(require_student)):
    user: models.User = ctx["user"]
    db: Session       = ctx["db"]

    # Get all class IDs this student is enrolled in
    enrolled_class_ids = [
        e.class_id
        for e in db.query(models.ClassEnrollment)
                   .filter(models.ClassEnrollment.student_id == user.id)
                   .all()
    ]

    if not enrolled_class_ids:
        return {"success": True, "exams": []}

    # Fetch all active exams for those classes
    exams = (
        db.query(models.Exam)
        .filter(
            models.Exam.class_id.in_(enrolled_class_ids),
            models.Exam.is_active == True,
        )
        .order_by(models.Exam.due_date.asc())
        .all()
    )

    result = []
    for exam in exams:
        # Load questions — hide correct_option and marking_guide from student
        questions = (
            db.query(models.ExamQuestion)
            .filter(models.ExamQuestion.exam_id == exam.id)
            .order_by(models.ExamQuestion.order_index)
            .all()
        )

        # Check if this student already submitted
        submission = (
            db.query(models.ExamSubmission)
            .filter(
                models.ExamSubmission.exam_id    == exam.id,
                models.ExamSubmission.student_id == user.id,
            )
            .first()
        )

        total_marks = sum(q.marks for q in questions)

        result.append({
            "id":          exam.id,
            "title":       exam.title,
            "description": exam.description,
            "instructions":exam.instructions,
            "due_date":    fmt_date(exam.due_date),
            "time_limit":  exam.time_limit,
            "total_marks": total_marks,
            "questions": [
                {
                    "id":      q.id,
                    "type":    q.type,
                    "prompt":  q.prompt,
                    "marks":   q.marks,
                    # Only send options for MCQ — never send correct_option or marking_guide
                    "options": json.loads(q.options) if q.options else None,
                }
                for q in questions
            ],
            "my_submission": _fmt_submission(submission) if submission else None,
        })

    return {"success": True, "exams": result}


# ═══════════════════════════════════════════════════════════════════════════════
#  POST /api/student/exams/submit
#  Accepts all answers, auto-grades MCQ, stores structured for teacher review.
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/exams/submit")
def submit_exam(
    body: SubmitExamRequest,
    x_csrf_token: Optional[str] = Header(default=None),
    ctx: dict = Depends(require_student),
):
    user: models.User           = ctx["user"]
    session: models.UserSession = ctx["session"]
    db: Session                 = ctx["db"]

    validate_csrf(session, x_csrf_token, body.csrf_token)

    # ── Validate exam exists and student is enrolled ───────────────────────────
    exam = db.query(models.Exam).filter(
        models.Exam.id        == body.exam_id,
        models.Exam.is_active == True,
    ).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")

    enrolled = db.query(models.ClassEnrollment).filter_by(
        class_id=exam.class_id,
        student_id=user.id,
    ).first()

    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this class.")

    # ── Check deadline ─────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    due = exam.due_date
    if due.tzinfo is None:
        due = due.replace(tzinfo=BLANTYRE)
    if now > due:
        raise HTTPException(status_code=422, detail="This exam is past its due date.")

    # ── Prevent double submission ──────────────────────────────────────────────
    existing = db.query(models.ExamSubmission).filter_by(
        exam_id=exam.id,
        student_id=user.id,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="You have already submitted this exam.")

    # ── Load all questions for this exam ───────────────────────────────────────
    questions = (
        db.query(models.ExamQuestion)
        .filter(models.ExamQuestion.exam_id == exam.id)
        .all()
    )
    question_map = {q.id: q for q in questions}

    # ── Build answer lookup from request ──────────────────────────────────────
    answer_map = {a.question_id: a for a in body.answers}

    # ── Auto-grade MCQ and tally score ────────────────────────────────────────
    mcq_score  = 0
    has_structured = False

    exam_submission = models.ExamSubmission(
        exam_id    = exam.id,
        student_id = user.id,
        status     = "submitted",
    )
    db.add(exam_submission)
    db.flush()  # get exam_submission.id

    for question in questions:
        student_answer = answer_map.get(question.id)

        if question.type == "mcq":
            selected = student_answer.selected_option if student_answer else None
            is_correct   = (selected == question.correct_option) if selected else False
            score_awarded = question.marks if is_correct else 0
            mcq_score    += score_awarded

            db.add(models.ExamAnswer(
                submission_id   = exam_submission.id,
                question_id     = question.id,
                selected_option = selected,
                is_correct      = is_correct,
                score_awarded   = score_awarded,
            ))

        elif question.type == "structured":
            has_structured = True
            answer_text    = student_answer.answer_text.strip() if (student_answer and student_answer.answer_text) else ""

            db.add(models.ExamAnswer(
                submission_id = exam_submission.id,
                question_id   = question.id,
                answer_text   = answer_text,
                is_correct    = None,   # teacher/AI grades this
                score_awarded = None,
            ))

    # ── Set total score and status ─────────────────────────────────────────────
    # If there are only MCQs we can finalise the score immediately.
    # If there are structured questions the score stays None until teacher grades.
    if not has_structured:
        exam_submission.total_score = mcq_score
        exam_submission.status      = "graded"
        exam_submission.graded_at   = datetime.now(timezone.utc)
    else:
        # Store the MCQ portion so the teacher sees it — full score after review
        exam_submission.total_score = None
        exam_submission.status      = "submitted"

    db.commit()
    db.refresh(exam_submission)

    return {
        "success": True,
        "message": (
            "Exam submitted and graded!"
            if not has_structured
            else "Exam submitted. Your structured answers are pending teacher review."
        ),
        "submission": _fmt_submission(exam_submission),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/student/exams/results
#  Returns all submitted exams with scores and per-answer feedback.
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/exams/results")
def get_exam_results(ctx: dict = Depends(require_student)):
    user: models.User = ctx["user"]
    db: Session       = ctx["db"]

    submissions = (
        db.query(models.ExamSubmission)
        .filter(models.ExamSubmission.student_id == user.id)
        .order_by(models.ExamSubmission.submitted_at.desc())
        .all()
    )

    results = []
    for sub in submissions:
        exam = db.query(models.Exam).filter(models.Exam.id == sub.exam_id).first()
        if not exam:
            continue

        questions = (
            db.query(models.ExamQuestion)
            .filter(models.ExamQuestion.exam_id == exam.id)
            .order_by(models.ExamQuestion.order_index)
            .all()
        )
        question_map = {q.id: q for q in questions}
        total_marks  = sum(q.marks for q in questions)

        answers = (
            db.query(models.ExamAnswer)
            .filter(models.ExamAnswer.submission_id == sub.id)
            .all()
        )

        answer_details = []
        for ans in answers:
            q = question_map.get(ans.question_id)
            if not q:
                continue

            detail = {
                "question_id":    q.id,
                "type":           q.type,
                "prompt":         q.prompt,
                "marks":          q.marks,
                "score_awarded":  ans.score_awarded,
                "ai_feedback":    ans.ai_feedback,
            }

            # Only reveal MCQ correct answer after submission is graded
            if q.type == "mcq" and sub.status == "graded":
                detail["selected_option"] = ans.selected_option
                detail["correct_option"]  = q.correct_option
                detail["is_correct"]      = ans.is_correct
                detail["options"]         = json.loads(q.options) if q.options else None
            elif q.type == "structured":
                detail["answer_text"] = ans.answer_text

            answer_details.append(detail)

        results.append({
            "submission_id": sub.id,
            "exam_id":       exam.id,
            "exam_title":    exam.title,
            "total_marks":   total_marks,
            "total_score":   sub.total_score,
            "status":        sub.status,
            "submitted_at":  fmt_date(sub.submitted_at),
            "graded_at":     fmt_date(sub.graded_at),
            "answers":       answer_details,
        })

    return {"success": True, "results": results}


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_submission(sub: models.ExamSubmission) -> dict:
    if not sub:
        return None
    return {
        "id":          sub.id,
        "status":      sub.status,
        "total_score": sub.total_score,
        "submitted_at":fmt_date(sub.submitted_at),
        "graded_at":   fmt_date(sub.graded_at),
    }