from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import CurrentUserOut, LoginRequest
from app.services.auth_service import AuthService, create_access_token
from app.utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: DbSession) -> dict[str, object]:
    user = AuthService(db).authenticate(payload.username, payload.password)
    token = create_access_token(user)
    return success_response(request, {"access_token": token, "token_type": "bearer"})


@router.get("/me")
def me(request: Request, user: CurrentUser) -> dict[str, object]:
    data = CurrentUserOut.model_validate(user, from_attributes=True).model_dump()
    return success_response(request, data)
