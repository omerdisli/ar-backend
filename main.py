import os
import time
import requests
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# Kiri Engine veya seçtiğiniz fotogrametri servisinin API anahtarı
PHOTOGRAMMETRY_API_KEY = "BURAYA_API_KEY_YAZIN"

@app.get("/")
def read_root():
    return {"status": "Gastrohackers 3D Photogrammetry Backend Aktif!"}

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    video_path = f"temp_{file.filename}"
    
    try:
        # 1. Gelen videoyu geçici olarak diske kaydet
        with open(video_path, "wb") as buffer:
            buffer.write(await file.read())

        # 2. Videoyu Fotogrametri API'sine gönder
        headers = {"Authorization": f"Bearer {PHOTOGRAMMETRY_API_KEY}"}
        
        with open(video_path, "rb") as f:
            files = {"file": (file.filename, f, "video/mp4")}
            # 3D Tarama görevi başlatma isteği
            upload_res = requests.post(
                "https://api.kiriengine.app/v1/reconstruct",
                headers=headers,
                files=files,
                data={"file_type": "video", "output_format": "glb"}
            ).json()

        task_id = upload_res.get("task_id")

        # 3. Modelin oluşmasını bekle (Polling)
        model_url = ""
        for _ in range(60):  # Maksimum 5 dakika (60 x 5 saniye)
            time.sleep(5)
            status_res = requests.get(
                f"https://api.kiriengine.app/v1/tasks/{task_id}",
                headers=headers
            ).json()

            if status_res.get("status") == "SUCCESS":
                model_url = status_res.get("glb_url")
                break
            elif status_res.get("status") == "FAILED":
                raise Exception("Fotogrametri işleme hatası oluştu.")

        # 4. Geçici video dosyasını temizle
        if os.path.exists(video_path):
            os.remove(video_path)

        # 5. Unity'ye üretilen 1:1 .glb modelinin indirme bağlantısını dön
        return {
            "status": "success",
            "model_url": model_url
        }

    except Exception as e:
        if os.path.exists(video_path):
            os.remove(video_path)
        return {"status": "error", "message": str(e)}
