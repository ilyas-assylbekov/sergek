# src/backend/main.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Header, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from pathlib import Path
import time
import uuid
from ml_processor import process_video
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import pandas as pd

class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/processed"):
            response.headers["Content-Type"] = "video/mp4"
            response.headers["Cache-Control"] = "no-cache"
        return response

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom header middleware
app.add_middleware(CustomHeaderMiddleware)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/processed", StaticFiles(directory="processed"), name="processed")

# Create necessary directories
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
for dir in [UPLOAD_DIR, PROCESSED_DIR]:
    dir.mkdir(exist_ok=True)

def get_unique_filename(original_filename: str) -> str:
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{unique_id}{ext}"

async def process_video_task(file_path: Path, output_path: Path):
    """Background task for video processing"""
    await process_video(str(file_path), str(output_path))

@app.get("/api/videos/predictions/{filename}")
async def get_predictions(filename: str):
    try:
        # Strip any video extension and get base filename
        base_filename = os.path.splitext(filename)[0]
        # Remove any "processed_" prefix if present
        base_filename = base_filename.replace('processed_', '')
        predictions_path = PROCESSED_DIR / f"{base_filename}_predictions.csv"
        
        print(f"Looking for predictions at: {predictions_path}")
        
        if not predictions_path.exists():
            # Try alternative filenames if the first attempt fails
            possible_paths = [
                PROCESSED_DIR / f"{base_filename}_predictions.csv",
                PROCESSED_DIR / f"processed_{base_filename}_predictions.csv",
                # Add more patterns if needed
            ]
            
            for path in possible_paths:
                if path.exists():
                    predictions_path = path
                    break
            else:  # If no file is found
                raise HTTPException(
                    status_code=404, 
                    detail=f"Predictions not found for {filename}. Tried paths: {[str(p) for p in possible_paths]}"
                )
            
        df = pd.read_csv(predictions_path)
        print(f"Loaded predictions data:\n{df.head()}")
        fps = int(df["FPS"].iloc[0]) if "FPS" in df.columns else 30
        
        # Convert the predictions to the expected format
        formatted_predictions = []
        for _, row in df.iterrows():
            formatted_predictions.append({
                "frame": int(row['Frame']),
                "bbox": eval(row['Bbox']) if isinstance(row['Bbox'], str) else row['Bbox'],
                "fps": fps
            })
        
        return {
            "predictions": formatted_predictions,
            "fps": fps
        }
        
    except Exception as e:
        print(f"Error processing predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        start_time = time.time()
        
        # Validate video file
        if not file.content_type.startswith('video/'):
            return {"error": "File must be a video"}, 400
        
        # Create unique filenames for both input and output
        unique_filename = get_unique_filename(file.filename)
        input_path = UPLOAD_DIR / unique_filename
        output_filename = f"processed_{unique_filename}"
        output_path = PROCESSED_DIR / output_filename
        
        # Save the uploaded file
        with open(input_path, "wb+") as file_object:
            file_object.write(await file.read())
        
        # Start processing in background
        background_tasks.add_task(
            process_video_task,
            input_path,
            output_path
        )
        
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
            
        return {
            "message": "Video uploaded and processing started",
            "filename": unique_filename,
            "processedFilename": output_filename,
            "originalFilename": file.filename,
            "size": os.path.getsize(input_path),
            "processingTime": processing_time,
            "status": "processing"
        }
    
    except Exception as e:
        # Fix error response format
        return {"error": str(e)}

@app.get("/api/videos/{filename}")
async def get_video_status(filename: str):
    """Check the status of video processing"""
    input_path = UPLOAD_DIR / filename
    output_path = PROCESSED_DIR / f"processed_{filename}"
    
    if not input_path.exists():
        return {"error": "Video not found"}, 404
        
    if output_path.exists():
        return {
            "status": "completed",
            "filename": filename,
            "processedFilename": f"processed_{filename}"
        }
    
    return {
        "status": "processing",
        "filename": filename
    }

@app.get("/api/videos/download/{filename}")
async def download_processed_video(
    filename: str,
    range: Optional[str] = Header(None)
):
    """Stream video with improved chunked transfer"""
    file_path = PROCESSED_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_size = file_path.stat().st_size

    # Handle range header for seeking support
    if range:
        start_bytes = int(range.replace("bytes=", "").split("-")[0])
        end_bytes = file_size - 1
        content_length = end_bytes - start_bytes + 1
        status_code = 206
    else:
        start_bytes = 0
        end_bytes = file_size - 1
        content_length = file_size
        status_code = 200

    headers = {
        "Content-Range": f"bytes {start_bytes}-{end_bytes}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Range, Content-Type",
    }

    async def stream_video():
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(file_path, "rb") as video:
            video.seek(start_bytes)
            remaining = content_length
            while remaining > 0:
                chunk = video.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        stream_video(),
        status_code=status_code,
        headers=headers
    )
