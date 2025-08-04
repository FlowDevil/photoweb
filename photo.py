from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from deepface import DeepFace
import os
import base64
import uuid
import shutil
import tempfile
import time


app = Flask(__name__,static_folder="static")
CORS(app)

DB_FOLDER = "facedb"
UPLOAD_FOLDER = './static/upload'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def download_matched_images_from_supabase(bucket_name: str, matched_paths: list, local_dir: str):
    os.makedirs(local_dir, exist_ok=True)
    downloaded_files = []

    for path in matched_paths:
        filename = os.path.basename(path)
        signed_url_data = supabase.storage.from_(bucket_name).create_signed_url(path, 60)
        signed_url = signed_url_data.get("signedURL")

        if signed_url:
            response = requests.get(signed_url)
            local_path = os.path.join(local_dir, filename)
            with open(local_path, "wb") as f:
                f.write(response.content)
            downloaded_files.append(local_path)
        else:
            print(f"Failed to get signed URL for {path}")
    return downloaded_files


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
                threshold=0.6,
                refresh_database=False
            )
            df = result[0]
            if not df.empty:
                vote_count += 1
                for i in range(len(df)):
                    full_path = df.iloc[i]["identity"]
                    filename = os.path.basename(full_path)
                    matched_images.add(filename)

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
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    copied_files = []
    try:
        bucket_name = "saudfcd"
        # Download only matched images
        copied_files = download_matched_images_from_supabase(bucket_name, matched_images, UPLOAD_FOLDER)
        except Exception as e:
            print(f"Error copying matched image: {path}", e)

    return jsonify({
        "match": True,
        "person": person_name,
        "matchedCount": vote_count,
        "matchedImages": [os.path.basename(p) for p in copied_files]
    })

from flask import send_from_directory
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True  # ⬅️ This tells the browser to download
    )

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
    return send_file(os.path.join(app.static_folder, "photo.html"))

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
