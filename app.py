
from flask import Flask, request, render_template_string, send_file
from PIL import Image
import cv2
import numpy as np
import io
import base64
import os
import zipfile

app = Flask(__name__)

HTML_FORM = """<!doctype html>
<html>
<head>
<title>REALITY投稿画像トリミング（プレビュー＋保存導線）</title>
<style>
  img.preview { max-height: 300px; margin: 10px; border: 1px solid #ccc; }
  .button-block { margin: 20px 0; text-align: center; }
  .button-block form { display: inline-block; margin: 0 10px; }
  .button-block input[type=submit] {
    font-size: 16px;
    padding: 10px 20px;
    background-color: #444;
    color: white;
    border: none;
    cursor: pointer;
  }
  .button-block input[type=submit]:hover {
    background-color: #666;
  }
</style>
</head>
<body>
<h2>REALITYスクショから投稿画像を自動切り出し（Y補正＋確認UI）</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=images multiple required accept="image/*">
  <input type=submit value='切り出し実行'>
</form>
<hr>
{% if previews %}
<h3>切り出し結果：</h3>
{% for p in previews %}
<img src="data:image/jpeg;base64,{{p}}" class="preview">
{% endfor %}

<div class="button-block">
  <form method="post" action="/download_zip">
    <input type="hidden" name="session_id" value="{{session_id}}">
    <input type="submit" value="✅ この切り出しでOK → ZIP保存">
  </form>

  <form method="get" action="/">
    <input type="submit" value="🔄 やり直す（別画像）">
  </form>
</div>
{% endif %}
</body>
</html>
"""

def detect_device(img: Image.Image):
    width, height = img.size
    if (width, height) == (706, 1536):
        return "iphone"
    elif (width, height) == (1009, 1537):
        return "ipad"
    else:
        return None

def detect_y_offset_from_ui(img: Image.Image) -> int:
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    search_region = img_cv[:100, :]
    _, thresh = cv2.threshold(search_region, 220, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 441
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    return y + h

@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        files = request.files.getlist("images")
        output_dir = "cropped"
        os.makedirs(output_dir, exist_ok=True)
        previews = []
        session_id = "current"

        for idx, file in enumerate(files):
            img = Image.open(file.stream)
            device = detect_device(img)
            if device not in ["iphone", "ipad"]:
                return f"非対応の画像サイズ：{img.size}"

            if device == "iphone":
                left, right = 16, 616
                top = detect_y_offset_from_ui(img) + 5
                crop_box = (left, top, right, top + 756)
            else:
                crop_box = (54, 450, 950, 1200)

            cropped = img.crop(crop_box)
            filename = f"{device}_cropped_{idx+1}.jpg"
            filepath = os.path.join(output_dir, filename)
            cropped.save(filepath)

            buffered = io.BytesIO()
            cropped.save(buffered, format="JPEG")
            b64img = base64.b64encode(buffered.getvalue()).decode("utf-8")
            previews.append(b64img)

        return render_template_string(HTML_FORM, previews=previews, session_id=session_id)

    return render_template_string(HTML_FORM, previews=None, session_id=None)

@app.route("/download_zip", methods=["POST"])
def download_zip():
    output_dir = "cropped"
    zip_path = "cropped_images.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(output_dir):
            zipf.write(os.path.join(output_dir, filename), filename)
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run()
