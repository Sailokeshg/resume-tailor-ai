from fastapi import FastAPI


def create_app():
    from .api.v1.api import api_router
    app = FastAPI(title="Resume Tailor AI")
    app.include_router(api_router, prefix="/api/v1")
    return app
