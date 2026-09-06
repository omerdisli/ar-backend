import time
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException

app = FastAPI()

KIRI_API_KEY = "SİZİN_KIRI_ENGINE_API_KEY_BURAYA"

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # 1. Adım: Unity'den gelen videoyu geçici olarak kaydet veya bellekten oku
    video_bytes = await file.read()
    
    # 2. Adım: Videoyu Kiri Engine API'ye gönder (Örn: Video Upload Endpoint)
    # Kiri Engine dokümantasyonuna göre istek atılır:
    url = "https://api.kiriengine.app/api/v1/open/photo/video"
    headers = {"Authorization": f"Bearer {KIRI_API_KEY}"}
    safe_filename = "dish_video.mp4"
    files = {"videoFile": (safe_filename, video_bytes, "video/mp4")}
    data = {"fileFormat": "glb", "modelQuality": "1"} # GLB formatı seçilir
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code != 200:
        return {"status": "error", "message": "Kiri Engine'e video yüklenemedi."}
    
    res_json = response.json()
    # Kiri Engine'den gelen benzersiz görev ID'si (serialize / task_id) alınır
    task_id = res_json.get("data", {}).get("serialize") 
    
    if not task_id:
        return {"status": "error", "message": "Görev ID alınamadı."}

    # 3. Adım: Modelin işlenmesini bekleyin veya Task ID'yi Unity'ye dönüp Unity'nin sormasını sağlayın.
    # (Eğer sunucu bekleyecekse aşağıdaki döngü kurulur - Render timeout sürelerine dikkat edilmelidir)
    
    model_glb_url = None
    max_try = 30  # Örneğin 30 kez kontrol et (~2.5 dakika)
    
    for _ in range(max_try):
        time.sleep(5) # 5 saniyede bir kontrol et
        status_url = f"https://api.kiriengine.app/api/v1/open/task/{task_id}"
        status_res = requests.get(status_url, headers=headers)
        status_data = status_res.json()
        
        # İşlem tamamlandıysa model indirme linkini al
        if status_data.get("data", {}).get("status") == "COMPLETED":
            model_glb_url = status_data.get("data", {}).get("modelUrl")
            break

    if model_glb_url:
        return {
    "status": "success",
    "model_url": model_glb_url,
    "message": "Model başarıyla oluşturuldu"
    }
    else:
        return {
            "status": "pending",
            "message": "Model hâlâ işleniyor, lütfen bekleyin..."
        }
