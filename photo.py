from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from deepface import DeepFace
import os
import base64
import uuid
import shutil
import tempfile
import time
import zipfile

app = Flask(__name__,static_folder="static")
CORS(app)

DB_FOLDER = "facedb"
UPLOAD_FOLDER = "uploads"
ZIP_PATH = "uploads.zip"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def decode_base64_to_image_file(base64_img):
    try:
        header, encoded = base64_img.split(",", 1)
        img_data = base64.b64decode(encoded)
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temp_file.write(img_data)
        temp_file.flush()
        temp_file.close()
        return temp_file.name
    except Exception as e:
        print("Error decoding base64 image:", e)
        return None


@app.route("/upload", methods=["POST"])
def upload_and_compare():
    data = request.get_json()
    images_data = data.get("images", [])
    person_name = data.get("name", "").strip()

    if not person_name:
        return jsonify({"message": "Name is required."}), 400

    if len(images_data) < 3:
        return jsonify({"message": "At least 3 images are required."}), 400

    person_folder = os.path.join(DB_FOLDER, person_name)
    if not os.path.isdir(person_folder):
        return jsonify({"message": f"No folder found for '{person_name}' in facedb."}), 404

    matched_images = set()
    vote_count = 0
    temp_files = []

    for base64_img in images_data:
        temp_path = decode_base64_to_image_file(base64_img)
        if not temp_path:
            continue
        temp_files.append(temp_path)

        try:
            result = DeepFace.find(
                img_path=temp_path,
                db_path=person_folder,
                model_name="ArcFace",
                enforce_detection=False,
                threshold=0.6
            )
            df = result[0]
            if not df.empty:
                vote_count += 1
                for i in range(len(df)):
                    matched_images.add(df.iloc[i]["identity"])

        except Exception as e:
            print(f"DeepFace error on {temp_path}:", e)

    for file_path in temp_files:
        try:
            os.remove(file_path)
        except:
            pass

    if vote_count == 0:
        time.sleep(3)
        return jsonify({"match": False, "message": "No match found."}), 404

    # Clear previous uploads
    shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)

    copied_files = []
    for path in matched_images:
        try:
            filename = os.path.basename(path)
            dest_path = os.path.join(UPLOAD_FOLDER, filename)
            shutil.copy2(path, dest_path)
            copied_files.append(dest_path)
        except Exception as e:
            print(f"Error copying matched image: {path}", e)

    # Create zip
    with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
        for file_path in copied_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))

    return jsonify({
        "match": True,
        "person": person_name,
        "matchedCount": vote_count,
        "zipAvailable": True
    })


@app.route("/download", methods=["GET"])
def download_zip():
    if os.path.exists(ZIP_PATH):
        return send_file(ZIP_PATH, as_attachment=True)
    else:
        return jsonify({"message": "ZIP file not found."}), 404


@app.route("/cleanup", methods=["POST"])
def cleanup():
    try:
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        return jsonify({"message": "Cleanup successful."})
    except Exception as e:
        return jsonify({"message": f"Cleanup error: {str(e)}"}), 500

@app.route("/")
def serve_index():
    return send_file(os.path.join(app.static_folder, "index.html"))

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
