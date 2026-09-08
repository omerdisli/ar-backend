import requests
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

# API Key'inizi tırnak işaretlerini silmeden araya yazın
KIRI_API_KEY = os.getenv("KIRI_API_KEY")
@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    video_bytes = await file.read()
    
    url = "https://api.kiriengine.app/api/v1/open/photo/video"
    headers = {"Authorization": f"Bearer {KIRI_API_KEY}"}
    
    safe_filename = "dish_video.mp4"
    files = {"videoFile": (safe_filename, video_bytes, "video/mp4")}
    data = {"fileFormat": "glb", "modelQuality": "1"}
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code != 200:
        return {"status": "error", "message": "Kiri Engine'e video yüklenemedi."}
    
    res_json = response.json()
    task_id = res_json.get("data", {}).get("serialize")
    
    if not task_id:
        return {"status": "error", "message": "Görev ID alınamadı."}

    return {
        "status": "processing",
        "task_id": task_id,
        "message": "Video işlenmeye başladı."
    }

@app.get("/check-status/{task_id}")
async def check_status(task_id: str):
    headers = {"Authorization": f"Bearer {KIRI_API_KEY}"}
    status_url = f"https://api.kiriengine.app/api/v1/open/task/{task_id}"
    
    status_res = requests.get(status_url, headers=headers)
    status_data = status_res.json()
    
    task_status = status_data.get("data", {}).get("status")
    
    if task_status == "COMPLETED":
        model_url = status_data.get("data", {}).get("modelUrl")
        return {
            "status": "success",
            "model_url": model_url,
            "message": "Model hazır!"
        }
    else:
        return {
            "status": "processing",
            "message": "Model henüz işleniyor..."
        }
