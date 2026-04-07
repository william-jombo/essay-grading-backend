


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes import auth, teacher, student, exams, student_exams

app = FastAPI(title="JomboEssayGrade API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://essaygrade.vercel.app",
        "https://jombo-essaygrade.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",    tags=["Auth"])
app.include_router(teacher.router,       prefix="/api/teacher", tags=["Teacher"])
app.include_router(student.router,       prefix="/api/student", tags=["Student"])
app.include_router(exams.router,         prefix="/api/teacher", tags=["Exams"])
app.include_router(student_exams.router, prefix="/api/student", tags=["Student Exams"])

@app.get("/")
def root():
    return {"message": "JomboEssayGrade API is running ✅"}