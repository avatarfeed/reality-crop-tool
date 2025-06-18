
import os
from zipfile import ZipFile
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import tempfile
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max total upload

MAX_FILES = 5
MAX_FILE_SIZE_MB = 5

def crop_image(image_path):
    # 仮の切り出し処理：画像中央を80%範囲でトリミング
    with Image.open(image_path) as img:
        w, h = img.size
        margin_w, margin_h = int(w * 0.1), int(h * 0.1)
        cropped = img.crop((margin_w, margin_h, w - margin_w, h - margin_h))
        return cropped

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('images')
        if not files or len(files) > MAX_FILES:
            return "アップロードは最大5枚までです。", 400

        with tempfile.TemporaryDirectory() as tmpdir:
            output_paths = []
            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    input_path = os.path.join(tmpdir, filename)
                    file.save(input_path)

                    # サイズ制限チェック
                    if os.stat(input_path).st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                        return f"{filename} は3MBを超えています。", 400

                    # 画像処理
                    cropped = crop_image(input_path)
                    output_filename = f"cropped_{uuid.uuid4().hex}.jpg"
                    output_path = os.path.join(tmpdir, output_filename)
                    cropped.save(output_path)
                    output_paths.append(output_path)

            zip_path = os.path.join(tmpdir, 'cropped_images.zip')
            with ZipFile(zip_path, 'w') as zipf:
                for path in output_paths:
                    zipf.write(path, os.path.basename(path))

            return send_file(zip_path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
