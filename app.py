from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
import os
import cv2
from PIL import Image
import numpy as np

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "ファイルが見つかりませんでした", 400
        file = request.files["file"]
        if file.filename == "":
            return "ファイルが選択されていません", 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 画像を読み込んで、上下UIを除いた中央部のみを切り出す
        img = cv2.imread(filepath)
        height, width, _ = img.shape
        top_crop = int(height * 0.10)
        bottom_crop = int(height * 0.11)
        cropped_img = img[top_crop:height - bottom_crop, :]

        processed_path = os.path.join(PROCESSED_FOLDER, "cropped_" + filename.split('.')[0] + ".png")
        cv2.imwrite(processed_path, cropped_img)

        return send_file(processed_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
