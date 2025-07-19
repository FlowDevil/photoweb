FROM python:3.10-slim

# Install required system libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the app port
EXPOSE 5000

# Use the Render-provided PORT env var if available
ENV PORT=5000

# Run the app with photo.py
CMD ["python", "photo.py"]
