from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_resume():
    return {"message": "Resume endpoint placeholder"}
