from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import tailor, resume

app = FastAPI(
    title="Resume Tailor AI",
    description="AI-powered resume tailoring using RAG and vector databases",
    version="1.0.0"
)

app.include_router(
    router=tailor.router,
    prefix="/api/v1/tailor",
    tags=["Tailor"]
)

app.include_router(
    router=resume.router,
    prefix="/api/v1/resume",
    tags=["Resume"]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Resume Tailor AI API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
