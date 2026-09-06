from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

# Fotoğrafların kaydedileceği klasör
UPLOAD_DIR = "uploaded_plates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-photos")
async def upload_photos():
    return {"status": "success", "message": "Fotograf paketi basariyla alindi!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
