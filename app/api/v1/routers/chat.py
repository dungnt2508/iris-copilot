from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.v1.dependencies import (
    get_current_user,
    require_permissions,
    get_user_repository,
)
from app.domain.user.repository import UserRepository


router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    query: str


@router.post("/query")
async def chat_query(
    payload: ChatRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    current_user=Depends(get_current_user),
    _perm=Depends(require_permissions("use:chat")),
):
    # TODO: call application use case (RAG pipeline)
    return {"answer": f"Echo: {payload.query}", "sources": []}


@router.get("/history")
async def chat_history(
    user_repo: UserRepository = Depends(get_user_repository),
    current_user=Depends(get_current_user),
):
    # TODO: implement fetching history per user/session
    return {"history": []}


@router.delete("/history")
async def clear_history(
    user_repo: UserRepository = Depends(get_user_repository),
    current_user=Depends(get_current_user),
):
    # TODO: implement delete history per user/session
    return {"status": "cleared"}

