import os
import requests
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gastrohackers 3D AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        file_bytes = await file.read()
        url = f"{KIRI_BASE_URL}/photo/video"
        headers = {
            "Authorization": f"Bearer {KIRI_API_KEY}"
        }
        
        files = {
            "videoFile": (file.filename, file_bytes, file.content_type)
        }
        
        data = {
            "fileFormat": "glb",
            "modelQuality": "1",
            "textureQuality": "1",
            "isMask": "1"
        }

        response = requests.post(url, headers=headers, files=files, data=data, timeout=90)

        try:
            res_data = response.json()
        except Exception:
            res_data = {}

        if response.status_code == 200 and res_data.get("code") == 200:
            data_obj = res_data.get("data")
            task_id = None

            if isinstance(data_obj, dict):
                task_id = (
                    data_obj.get("serialize") 
                    or data_obj.get("task_id") 
                    or data_obj.get("taskId") 
                    or data_obj.get("id")
                )
            elif isinstance(data_obj, str):
                task_id = data_obj
            
            if not task_id:
                task_id = res_data.get("serialize") or res_data.get("task_id") or res_data.get("taskId")

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
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@app.get("/check-status/{task_id}")
def check_status(task_id: str):
    if not KIRI_API_KEY:
        return {"status": "error", "message": "KIRI_API_KEY sunucuda tanımlı değil!"}

    try:
        url = f"{KIRI_BASE_URL}/photo/get-task-status"
        headers = {
            "Authorization": f"Bearer {KIRI_API_KEY}"
        }

        response = requests.get(url, headers=headers, params={"serialize": task_id}, timeout=30)
        
        if response.status_code != 200:
            response = requests.get(url, headers=headers, params={"task_id": task_id}, timeout=30)

        if response.status_code != 200:
            response = requests.get(url, headers=headers, params={"taskId": task_id}, timeout=30)

        if response.status_code in [500, 404, 502, 503]:
            return {
                "status": "processing",
                "message": f"Kiri Engine görevi hazırlıyor ({response.status_code}), bekleniyor..."
            }

        try:
            res_data = response.json()
        except Exception:
            res_data = {}

        if response.status_code == 200 and res_data.get("code") == 200:
            data = res_data.get("data", {})
            raw_status = data.get("status") if data.get("status") is not None else data.get("state")
            task_status_str = str(raw_status).upper()

            model_url = (
                data.get("model_url") 
                or data.get("fileUrl") 
                or data.get("glbUrl") 
                or data.get("downloadUrl")
                or data.get("resultUrl")
            )

            if task_status_str in ["SUCCESS", "FINISHED", "2", "COMPLETED"] or model_url:
                return {
                    "status": "success",
                    "model_url": model_url,
                    "message": "Model hazır!"
                }
            elif task_status_str in ["FAILED", "ERROR", "3", "4"]:
                return {
                    "status": "error",
                    "message": f"Kiri Engine işleme hatası (Durum: {raw_status})."
                }
            else:
                return {
                    "status": "processing",
                    "message": f"Model işleniyor... (Durum: {raw_status})"
                }
        else:
            error_msg = res_data.get("msg") or res_data.get("message") or response.text or "Durum bekleniyor..."
            return {
                "status": "processing",
                "message": f"Görsel işleniyor: {error_msg}"
            }

    except Exception as e:
        return {"status": "processing", "message": f"İstek yeniden deneniyor: {str(e)}"}
