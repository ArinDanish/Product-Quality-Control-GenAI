from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from visionllm import compare_with_gemini
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Quality Control API",
    description="AI-powered product quality comparison using Gemini Vision",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Product Quality Control API is running",
        "version": "1.0.0"
    }


@app.post("/compare")
async def compare_images(
    perfect: UploadFile = File(..., description="Reference/perfect product image"),
    defective: UploadFile = File(..., description="Test product image to analyze")
):
    """
    Compare two product images and identify defects
    
    Args:
        perfect: Reference image (perfect product)
        defective: Test image to analyze
        
    Returns:
        Quality analysis with score, defects, and recommendation
    """
    try:
        # Validate file types
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if perfect.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Perfect image must be JPEG or PNG, got {perfect.content_type}"
            )
        if defective.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Defective image must be JPEG or PNG, got {defective.content_type}"
            )
        
        logger.info(f"Comparing images: {perfect.filename} vs {defective.filename}")
        
        # Read image bytes
        perfect_bytes = await perfect.read()
        defective_bytes = await defective.read()
        
        # Validate file sizes (max 10MB each)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(perfect_bytes) > max_size or len(defective_bytes) > max_size:
            raise HTTPException(
                status_code=400,
                detail="Image size must be less than 10MB"
            )
        
        # Perform comparison
        result = compare_with_gemini(perfect_bytes, defective_bytes)
        
        if "error" in result:
            logger.error(f"Comparison error: {result['error']}")
            raise HTTPException(status_code=500, detail=result['error'])
        
        logger.info(f"Analysis complete - Score: {result.get('quality_score')}/10")
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    import os
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "service": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)