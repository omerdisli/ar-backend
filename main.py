from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Gastrohackers 3D AI Backend Aktif!"}

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # Gelen .mp4 videosunu geçici kaydet
    video_path = f"temp_{file.filename}"
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {
        "status": "success",
        "message": "Video başarıyla sunucuya ulaştı!",
        "filename": file.filename
    }
