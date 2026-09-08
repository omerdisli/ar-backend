import os
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gastrohackers Polycam API Backend")

# Unity / Web erişimi için CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render Environment Variables üzerinden Polycam API Key okunur
POLYCAM_API_KEY = os.getenv("POLYCAM_API_KEY", "")
POLYCAM_BASE_URL = "https://api.poly.cam/v1"

@app.get("/")
def read_root():
    return {
        "status": "Gastrohackers 3D AI Backend Aktif!",
        "engine": "Polycam API"
    }

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Unity'den gelen MP4 videosunu alır ve Polycam API sunucularına işlenmek üzere gönderir.
    """
    if not POLYCAM_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="POLYCAM_API_KEY ortam değişkeni ayarlanmamış!"
        )

    try:
        # Video içeriğini oku
        contents = await file.read()
        
        headers = {
            "Authorization": f"Bearer {POLYCAM_API_KEY}"
        }

        files = {
            "file": (file.filename, contents, file.content_type or "video/mp4")
        }

        # Polycam ham veri / video yükleme endpoint'ine istek at
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{POLYCAM_BASE_URL}/captures/upload",
                headers=headers,
                files=files
            )

            if response.status_code not in [200, 201]:
                return {
                    "status": "error",
                    "message": f"Polycam API Hatası ({response.status_code}): {response.text}"
                }

            data = response.json()
            # Polycam'den dönen işlem/tarama ID'si
            task_id = data.get("id") or data.get("capture_id") or data.get("task_id")

            if not task_id:
                return {
                    "status": "error",
                    "message": f"Polycam Yanıtından Task ID alınamadı: {data}"
                }

            return {
                "status": "processing",
                "task_id": task_id,
                "message": "Video Polycam sunucularına yüklendi, işleniyor..."
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Sunucu iç hatası: {str(e)}"
        }

@app.check_status = app.get("/check-status/{task_id}")
@app.get("/check-status/{task_id}")
async def check_status(task_id: string):
    """
    Polycam API'den 3D model çıkarma işleminin durumunu sorgular.
    Tamamlandığında .glb modelinin URL'sini döndürür.
    """
    if not POLYCAM_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="POLYCAM_API_KEY ortam değişkeni ayarlanmamış!"
        )

    try:
        headers = {
            "Authorization": f"Bearer {POLYCAM_API_KEY}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{POLYCAM_BASE_URL}/captures/{task_id}",
                headers=headers
            )

            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Polycam Durum Hatası ({response.status_code}): {response.text}"
                }

            data = response.json()
            processing_status = data.get("status", "").lower()

            # Polycam işlemi tamamlandıysa
            if processing_status in ["completed", "success", "finished"]:
                # GLB formatındaki model linkini bul
                exports = data.get("exports", {})
                glb_url = exports.get("glb") or data.get("glb_url") or data.get("download_url")

                if glb_url:
                    return {
                        "status": "success",
                        "model_url": glb_url,
                        "message": "3D Model başarıyla üretildi!"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Polycam işlemi tamamlandı ancak GLB indirme linki bulunamadı."
                    }

            elif processing_status in ["failed", "error"]:
                return {
                    "status": "error",
                    "message": f"Polycam işleme hatası: {data.get('error', 'Bilinmeyen hata')}"
                }

            else:
                return {
                    "status": "processing",
                    "message": f"Görsel işleniyor... (Polycam Durum: {processing_status or 'İşleniyor'})"
                }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Bağlantı sorgu hatası: {str(e)}"
        }
