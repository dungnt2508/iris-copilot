from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.api.v1.dependencies import (
    get_token_service,
    get_current_user,
    require_roles,
    require_permissions,
    get_user_repository,
)
from app.domain.user.repository import UserRepository
from app.api.v1.dependencies import get_user_repository


router = APIRouter(tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user=Depends(get_current_user),
    _perm=Depends(require_permissions("write:documents")),
):
    # TODO: validate extension, route to application use case to process & index
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required")
    return {"filename": file.filename, "status": "received"}


@router.get("")
async def list_documents(
    user_repo: UserRepository = Depends(get_user_repository),
    current_user=Depends(get_current_user),
    _perm=Depends(require_permissions("read:documents")),
):
    # TODO: implement list documents for current user
    return {"items": []}

