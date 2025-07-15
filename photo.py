from flask import Flask, request, jsonify
from flask_cors import CORS
from deepface import DeepFace
import os
import base64
import uuid
import shutil
import tempfile

app = Flask(__name__)

CORS(app)

DB_FOLDER = "facedb"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def decode_base64_to_image_file(base64_img):
    """
    Decodes base64 string to a temporary image file and returns the path.
    """
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
                threshold=0.6  # Adjust similarity threshold if needed
            )
            df = result[0]
            print(f"Result DataFrame for image {temp_path}:\n", df)

            if not df.empty:
                vote_count += 1
                for i in range(len(df)):
                    matched_images.add(df.iloc[i]["identity"])

        except Exception as e:
            print(f"DeepFace error on {temp_path}:", e)

    # Cleanup temp files
    for file_path in temp_files:
        try:
            os.remove(file_path)
        except:
            pass

    if vote_count == 0:
        return jsonify({"match": False, "message": "No match found."}), 404

    copied_files = []
    for path in matched_images:
        try:
            filename = os.path.basename(path)
            dest_path = os.path.join(UPLOAD_FOLDER, filename)
            shutil.copy2(path, dest_path)
            copied_files.append(dest_path)
        except Exception as e:
            print(f"Error copying matched image: {path}", e)

    return jsonify({
        "match": True,
        "person": person_name,
        "matchedCount": vote_count,
        "matchedImages": copied_files
    })


if __name__ == "__main__":
    app.run(debug=True)
