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

# テンプレートの読み込み
dot_template = cv2.imread('template_dot_menu.png', cv2.IMREAD_GRAYSCALE)
plus_template = cv2.imread('template_plus_icon.png', cv2.IMREAD_GRAYSCALE)

if dot_template is None or plus_template is None:
    print("テンプレート読み込みに失敗しました。")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def match_template_y(gray_img, template):
    res = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    return max_loc[1], max_val

def crop_ui_using_templates(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    dot_y, dot_score = match_template_y(gray, dot_template)
    plus_y, plus_score = match_template_y(gray, plus_template)

    print(f"dot_y: {dot_y} (score: {dot_score:.3f}), plus_y: {plus_y} (score: {plus_score:.3f})")

    top = dot_y + 60
    bottom = plus_y - 30

    if bottom <= top or dot_score < 0.3 or plus_score < 0.3:
        print("テンプレート検出に失敗。バックアップ範囲で切り取り")
        top = 180
        bottom = img.shape[0] - 140

    cropped = img[top:bottom, :]
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

                cropped_img = crop_ui_using_templates(file_path)
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
