from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from contextlib import asynccontextmanager
import json
import os
import asyncio

# Import your existing RAG system
from rag import rag_chain, llm, create_rag_chain, generate_lesson, Pace
from dataLoading import initialize_vectorstore, check_status
from dataLoading import vectorstore # Ensure vectorstore is imported

# Pydantic models for request/response
class LessonRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="The mathematics topic for the lesson")
    sss_level: Literal["SSS 1", "SSS 2", "SSS 3"] = Field(..., description="The Senior Secondary School level")
    learning_pace: Pace = Field(..., description="The student's learning pace (low, moderate, advance)")


class SourceDocument(BaseModel):
    source: str
    page: Optional[int]
    content_preview: str


class LessonResponse(BaseModel):
    topic: str
    sss_level: str
    learning_pace: str
    lesson_notes: str
    sources: List[SourceDocument]
    status: str = "success"


class ErrorResponse(BaseModel):
    error: str
    status: str = "error"


class RebuildResponse(BaseModel):
    message: str
    status: str
    metadata: dict


# Global variable to hold the RAG chain
current_rag_chain = None


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    global current_rag_chain

    # Startup
    print("=" * 80)
    print("🇸🇱 SSS AI Tutor API Starting...")
    print("=" * 80)

    # Load cached vectorstore (will be fast after first build)
    current_rag_chain = rag_chain
    print("✅ RAG Chain initialized with cached vectorstore.")

    yield # Application runs

    # Shutdown
    print("=" * 80)
    print("API Shutdown Complete.")
    print("=" * 80)


# Initialize the FastAPI application
app = FastAPI(
    title="SSS AI Mathematics Tutor API",
    description="An AI platform providing personalized lessons based on the SSS Mathematics curriculum.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "app": "sss-ai-tutor"}


@app.get("/status")
async def get_status():
    """Get the current status and metadata of the vectorstore"""
    return check_status()


@app.post("/rebuild", response_model=RebuildResponse)
async def rebuild_vectorstore_endpoint():
    """Forces a rebuild of the vectorstore from the source documents."""
    global current_rag_chain
    try:
        # Run rebuild in a threadpool to prevent blocking the event loop
        new_vectorstore, _ = await asyncio.to_thread(initialize_vectorstore, force_rebuild=True)
        # Update the global RAG chain with the new vectorstore
        current_rag_chain = create_rag_chain(new_vectorstore, llm)
        metadata = check_status()
        return RebuildResponse(
            message="Vectorstore successfully rebuilt and RAG chain updated.",
            status="success",
            metadata=metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/lesson", response_model=LessonResponse, responses={500: {"model": ErrorResponse}})
async def create_lesson(request: LessonRequest):
    """Generates a personalized lesson based on topic, SSS level, and learning pace."""
    if current_rag_chain is None:
        raise HTTPException(
            status_code=503, 
            detail="RAG system is not initialized. Check /status and try rebuilding the vectorstore."
        )

    full_level = request.sss_level
    topic = request.topic
    pace = request.learning_pace
    
    # We call the RAG chain directly using the logic from the `generate_lesson` function
    print(f"API Request: Generating lesson for {topic} ({full_level}, {pace} pace)")

    try:
        # The chain expects a single query, but we pass extra context variables
        result = await asyncio.to_thread(
            current_rag_chain.invoke, 
            {
                "query": f"Generate a lesson on {topic} for {full_level} students with a {pace} learning pace.",
                "topic": topic,
                "level": full_level,
                "pace": pace
            }
        )

        # Process source documents for the response model
        sources = []
        if 'source_documents' in result:
            for doc in result['source_documents']:
                sources.append(SourceDocument(
                    source=doc.metadata.get('source', 'Curriculum Syllabus'),
                    page=doc.metadata.get('page', 0) + 1, # Page number is 0-indexed in PDF loader
                    content_preview=doc.page_content[:150] + "..."
                ))

        return LessonResponse(
            topic=topic,
            sss_level=full_level,
            learning_pace=pace,
            lesson_notes=result['result'],
            sources=sources
        )

    except Exception as e:
        print(f"Error during lesson generation: {e}")
        raise HTTPException(status_code=500, detail=f"Lesson generation failed: {str(e)}")


@app.get("/examples")
async def get_examples():
    """Get example parameters you can use for the lesson generation."""
    return {
        "examples": [
            {"topic": "Integers and Rational Numbers", "sss_level": "SSS 1", "learning_pace": "low"},
            {"topic": "Vectors in 3D (Dot Product)", "sss_level": "SSS 3", "learning_pace": "advance"},
            {"topic": "Quadratic Equations (Factorization)", "sss_level": "SSS 2", "learning_pace": "moderate"},
        ],
        "tips": [
            "Use topics found in the SSS Mathematics for STEAMM syllabus for best results.",
            "Test different learning paces (low, moderate, advance) to see the personalization.",
            "The system uses your SSS curriculum PDF as its knowledge base."
        ]
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 80)
    print("🚀 Starting SSS AI Tutor API...")
    print("=" * 80)
    print("📖 Interactive docs: http://localhost:8000/docs")
    print("💡 Example lessons: http://localhost:8000/examples")
    print("🏥 Health check: http://localhost:8000/health")
    print("🔄 Rebuild vectorstore: http://localhost:8000/rebuild (POST)")
    print("📊 Check status: http://localhost:8000/status")
    print("=" * 80 + "\n")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )