from fastapi import Depends, FastAPI, APIRouter

from onboard_agent.api.security import verify_token

router=APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Public route/no token required"""
    return {"status": "ok"}


@router.post("/chat")
def chat(_token: str = Depends(verify_token)) -> dict[str, str]:
    """Protected route/requires Authorization"""
    return {"message": "You are authenticated!"}
