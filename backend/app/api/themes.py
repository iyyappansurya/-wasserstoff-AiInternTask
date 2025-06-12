from fastapi import APIRouter, Request
from app.services import themeSummarize

router = APIRouter()

@router.post("/")
async def synthesize_themes(request: Request):
    body = await request.json()
    answers = body.get("answers")
    result = themeSummarize.summarize_themes(answers)
    return {"themes": result}
