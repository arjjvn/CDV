from fastapi import APIRouter, Depends
from Backend.auth.dependencies import get_current_user

router=APIRouter(prefix="/user",tags=["Users"])
@router.get("/me")
def read_current_user(
    current_user:dict=Depends(get_current_user),
):
    return {
        "message":"You are authenticated!",
        "user_id":current_user["user_id"],
    }