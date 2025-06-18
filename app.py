from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
import numpy as np
import os
import io
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def crop_ui_from_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)

    # 水平方向（上下）の黒帯検出（左右方向の検出は無視）
    horizontal_projection = np.sum(thresh == 0, axis=1)
    height, width = img.shape[:2]
    top, bottom = 0, height - 1
    threshold = width * 0.6  # 横幅の60%以上が暗ければ黒帯とみなす

    for i, val in enumerate(horizontal_projection):
        if val < threshold:
            top = i
            break
    for i in range(len(horizontal_projection)-1, -1, -1):
        if horizontal_projection[i] < threshold:
            bottom = i
            break

    cropped = img[top:bottom, :]  # 横方向は削らない
    return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('file')
        result_files = []

        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                cropped_img = crop_ui_from_image(file_path)
                result_path = os.path.join(RESULT_FOLDER, filename.rsplit('.', 1)[0] + ".png")
                cropped_img.save(result_path, format='PNG')
                result_files.append(result_path)

        if len(result_files) == 1:
            return send_file(result_files[0], as_attachment=True)
        elif len(result_files) > 1:
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, 'w') as zipf:
                for f in result_files:
                    zipf.write(f, os.path.basename(f))
            zip_io.seek(0)
            return send_file(zip_io, mimetype='application/zip', download_name='cropped_images.zip', as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
