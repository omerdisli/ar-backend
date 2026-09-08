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

# Render Environment Variables üzerinden API anahtarını alıyoruz
KIRI_API_KEY = os.getenv("KIRI_API_KEY")
KIRI_BASE_URL = "https://api.kiriengine.app/api/v1/open"


@app.get("/")
def read_root():
    return {"status": "Gastrohackers 3D AI Backend Aktif!"}


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    if not KIRI_API_KEY:
        print("[ERROR] KIRI_API_KEY sunucuda tanımlı değil!")
        return {"status": "error", "message": "KIRI_API_KEY sunucuda tanımlı değil!"}

    try:
        file_bytes = await file.read()
        url = f"{KIRI_BASE_URL}/photo/video"
        headers = {
            "Authorization": f"Bearer {KIRI_API_KEY}"
        }
        
        # Kiri Engine API 'videoFile' parametre adı bekliyor
        files = {
            "videoFile": (file.filename, file_bytes, file.content_type)
        }
        
        # Format ve kalite parametreleri
        data = {
            "fileFormat": "glb",
            "modelQuality": "1",
            "textureQuality": "1",
            "isMask": "1"
        }

        print(f"[LOG] Kiri Engine'e istek atılıyor: {url}")
        print(f"[LOG] Dosya Adı: {file.filename}, Boyut: {len(file_bytes)} bytes")

        response = requests.post(url, headers=headers, files=files, data=data, timeout=90)

        print(f"[LOG] Kiri Engine HTTP Status: {response.status_code}")
        print(f"[LOG] Kiri Engine Yanıt Metni: {response.text}")

        try:
            res_data = response.json()
        except Exception:
            res_data = {}

        if response.status_code == 200 and res_data.get("code") == 200:
            data_obj = res_data.get("data")
            task_id = None

            # Kiri Engine'in dönebileceği tüm task_id formatlarını tarıyoruz
            if isinstance(data_obj, dict):
                task_id = data_obj.get("task_id") or data_obj.get("taskId") or data_obj.get("id") or data_obj.get("taskID")
            elif isinstance(data_obj, str):
                task_id = data_obj
            
            if not task_id:
                task_id = res_data.get("task_id") or res_data.get("taskId") or res_data.get("id")

            if task_id:
                return {
                    "status": "processing",
                    "task_id": task_id,
                    "message": "Video Kiri Engine'e başarıyla iletildi."
                }
            else:
                return {
                    "status": "error",
                    "message": f"Task ID okunamadı. Kiri Yanıtı: {response.text}"
                }
        else:
            error_msg = res_data.get("msg") or res_data.get("message") or response.text or "Kiri Engine bilinmeyen hata."
            return {
                "status": "error",
                "message": f"Kiri Engine Hatası ({response.status_code}): {error_msg}"
            }

    except Exception as e:
        print(f"[EXCEPT] Sunucu içi hata: {str(e)}")
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


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
        
        try:
            res_data = response.json()
        except Exception:
            res_data = {}

        if response.status_code == 200 and res_data.get("code") == 200:
            data = res_data.get("data", {})
            task_status = str(data.get("status", "")).upper()

            if task_status in ["SUCCESS", "FINISHED"] or data.get("model_url"):
                model_url = data.get("model_url") or data.get("fileUrl") or data.get("glbUrl")
                return {
                    "status": "success",
                    "model_url": model_url,
                    "message": "Model hazır!"
                }
            elif task_status in ["FAILED", "ERROR"]:
                return {
                    "status": "error",
                    "message": "Kiri Engine model işleme hatası verdi."
                }
            else:
                return {
                    "status": "processing",
                    "message": f"Model işleniyor... (Durum: {task_status})"
                }
        else:
            error_msg = res_data.get("msg") or res_data.get("message") or "Durum sorgulanamadı."
            return {
                "status": "error",
                "message": error_msg
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
