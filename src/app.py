from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
import logging
import os
import io
import pyheif
from PIL import Image

from src.config import Config

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert_image():
    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        heif_file = pyheif.read(file_path)
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )

        png_io = io.BytesIO()
        image.save(png_io, format="PNG")
        png_io.seek(0)
        os.remove(file_path)

        return send_file(
            png_io,
            mimetype="image/png",
            download_name=filename.rsplit(".", 1)[0] + ".png",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app_env = os.getenv("FLASK_ENV", "development")
    port = int(os.getenv("PORT", 5000))
    debug = True

    if app_env != "development":
        debug = False

    app.run(debug=debug, host="0.0.0.0", port=port)
