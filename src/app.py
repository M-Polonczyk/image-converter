from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
import logging
import os
import io
import pyheif
from PIL import Image
from moviepy import VideoFileClip

from src.config import Config

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert/image", methods=["POST"])
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


@app.route("/convert/video", methods=["POST"])
def convert_video():
    if "video" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["video"]
    if not file.filename:
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    output_filename = filename.rsplit(".", 1)[0] + ".mp4"
    output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_filename)
    
    try:
        file.save(file_path)
        
        # Load the video file
        video = VideoFileClip(file_path)
        
        # Convert to MP4 with H.264 codec
        video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Close the video file to free resources
        video.close()
        
        # Remove the original file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Read the converted file for response
        with open(output_path, 'rb') as f:
            video_data = f.read()
        
        # Remove the converted file after reading
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Create BytesIO object for sending
        video_io = io.BytesIO(video_data)
        video_io.seek(0)
        
        return send_file(
            video_io,
            mimetype="video/mp4",
            download_name=output_filename,
            as_attachment=True
        )

    except Exception as e:
        # Clean up files in case of error
        for file_to_remove in [file_path, output_path]:
            if os.path.exists(file_to_remove):
                try:
                    os.remove(file_to_remove)
                except Exception:
                    pass
        
        logger.error("Video conversion error: %r", e)
        return jsonify({"error": "Video conversion failed"}), 500


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app_env = os.getenv("FLASK_ENV", "development")
    port = int(os.getenv("PORT", 5000))
    debug = app_env == "development"

    app.run(debug=debug, host="0.0.0.0", port=port)
