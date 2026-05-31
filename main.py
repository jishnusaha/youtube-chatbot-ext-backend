from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_pipeline import get_question_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://kadppppjdgoggfglloaonfblhemlnlmo",
        "http://localhost:5173/",  # if you test from a local frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}


class AskRequest(BaseModel):
    video_id: str
    question: str
    session_id: str


@app.post("/ask")
async def ask(request: AskRequest):
    try:
        answer = get_question_answer(
            request.video_id, request.session_id, request.question
        )
        return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
