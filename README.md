📷 Smart Face Recognition Web App A web-based face recognition system using python Flask, DeepFace, and HTML/CSS/JS. It captures images via webcam, compares them with a saved face database, and highlights matches. Useful for authentication, attendance, or identity verification systems.

## 🚀 Features

- ✅ Capture 3 face images (front, left, right)
- ✅ Beautiful loader animation during upload
- ✅ Toast notifications for user guidance
- ✅ Camera access with fallback handling
- ✅ Image preview with delete option
- ✅ Upload to Flask server via API
- ✅ Download ZIP and cleanup feature after processing

---

## 🧠 How It Works

1. **Start Camera:**
   - When the "Start Camera" button is clicked, the camera is accessed using `getUserMedia()`.
   - The video feed is shown.

2. **Capture Face:**
   - The user is prompted to capture:
     - 🧍 Front view
     - ↩️ Left profile
     - ↪️ Right profile
   - Each capture adds an image with a delete button.

3. **Stop Camera:**
   - Video feed stops.
   - Captured images move to the main form section.

4. **Submit Form:**
   - Form sends:
     - Name
     - 3 captured images (as Base64 strings)
   - Data sent via POST to `/upload`.

5. **Backend (Flask):**
   - Receives JSON with name & image data
   - Saves images
   - Processes (e.g. face match or database upload)
   - Sends JSON response back with match status

6. **After Upload:**
   - Loader hides
   - Shows match result (✅ or ❌)
   - Offers:
     - Download ZIP of images
     - Cleanup to reset session