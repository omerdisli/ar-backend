import os
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gastrohackers 3D AI Backend")

# Unity ve dış istekler için CORS izni
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render Environment Variables (Ortam Değişkenleri) üzerinden API anahtarını alıyoruz
KIRI_API_KEY = os.getenv("KIRI_API_KEY")
KIRI_BASE_URL = "https://api.kiriengine.app/api/v1/open"


@app.get("/")
def read_root():
    return {"status": "Gastrohackers 3D AI Backend Aktif!"}


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    if not KIRI_API_KEY:
        return {"status": "error", "message": "KIRI_API_KEY sunucuda tanımlı değil!"}

    try:
        # Unity'den gelen video verisini okuyoruz
        file_bytes = await file.read()

        url = f"{KIRI_BASE_URL}/photo/video"
        headers = {
            "Authorization": f"Bearer {KIRI_API_KEY}"
        }
        files = {
            "file": (file.filename, file_bytes, file.content_type)
        }

        # Kiri Engine API'sine videoyu iletiyoruz
        response = requests.post(url, headers=headers, files=files, timeout=60)
        res_data = response.json()

        if response.status_code == 200 and res_data.get("code") == 200:
            task_id = res_data.get("data", {}).get("task_id") or res_data.get("data", {}).get("taskId")
            return {
                "status": "processing",
                "task_id": task_id,
                "message": "Video Kiri Engine'e başarıyla iletildi."
            }
        else:
            return {
                "status": "error",
                "message": res_data.get("msg", "Kiri Engine'e video yüklenemedi.")
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/check-status/{task_id}")
def check_status(task_id: str):
    if not KIRI_API_KEY:
        return {"status": "error", "message": "KIRI_API_KEY sunucuda tanımlı değil!"}

    try:
        url = f"{KIRI_BASE_URL}/photo/get-task-status?task_id={task_id}"
        headers = {
            "Authorization": f"Bearer {KIRI_API_KEY}"
        }

        response = requests.get(url, headers=headers, timeout=30)
        res_data = response.json()

        if response.status_code == 200 and res_data.get("code") == 200:
            data = res_data.get("data", {})
            task_status = str(data.get("status", "")).upper()

            if task_status == "SUCCESS" or data.get("model_url"):
                model_url = data.get("model_url") or data.get("fileUrl") or data.get("glbUrl")
                return {
                    "status": "success",
                    "model_url": model_url,
                    "message": "Model hazır!"
                }
            elif task_status in ["FAILED", "ERROR"]:
                return {
                    "status": "error",
                    "message": "Kiri Engine model işleme hatası."
                }
            else:
                return {
                    "status": "processing",
                    "message": "Model işleniyor..."
                }
        else:
            return {
                "status": "error",
                "message": res_data.get("msg", "Durum sorgulanamadı.")
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
