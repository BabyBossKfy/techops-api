"""Route de l'assistant IA sur les procédures techniques."""

from fastapi import APIRouter, Depends, Request

from app.ai.assistant import ProcedureAssistant
from app.models import User
from app.schemas import AskRequest, AskResponse
from app.security import get_current_user

router = APIRouter(prefix="/assistant", tags=["Assistant IA"])


def get_assistant(request: Request) -> ProcedureAssistant:
    return request.app.state.assistant


@router.post("/ask", response_model=AskResponse)
def ask(
    data: AskRequest,
    assistant: ProcedureAssistant = Depends(get_assistant),
    _user: User = Depends(get_current_user),
) -> dict:
    return assistant.answer(data.question)
