
import io
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

app = FastAPI()

def detect_feed_area(image: np.ndarray) -> np.ndarray:
    # 画像の高さと幅を取得
    h, w, _ = image.shape

    # アバター画像下端（上端からおおよそ170px）
    top_crop = 170
    # ハート・コメントアイコン上端（下端からおおよそ150px）
    bottom_crop = 150

    # 上下を切り取り
    cropped = image[top_crop:h - bottom_crop, :]
    return cropped

@app.post("/crop")
async def crop_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    cropped_img = detect_feed_area(img)

    # PNG形式で保存
    _, png_img = cv2.imencode(".png", cropped_img)
    return StreamingResponse(io.BytesIO(png_img.tobytes()), media_type="image/png")
