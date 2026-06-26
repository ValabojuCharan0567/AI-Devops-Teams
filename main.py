"""FastAPI application initialization"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.config import settings
from api.routes import router
from app import __version__


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    print(f"🚀 Starting AI DevOps Team v{__version__}")
    print(f"📝 Environment: {settings.env}")
    print(f"🧠 LLM Provider: {settings.llm_provider}")
    if settings.llm_provider.lower() == "openai":
        print(f"🔑 OpenAI Model: {settings.openai_model}")
    else:
        print(f"🔧 Local LLM URL: {settings.local_llm_url}")
    yield
    print("👋 Shutting down AI DevOps Team")


app = FastAPI(
    title=settings.api_title,
    version=__version__,
    description="Multi-agent AI system for automating DevOps incident investigation",
    lifespan=lifespan,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
