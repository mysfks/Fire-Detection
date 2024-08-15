# Video Frame Extraction and Fire Detection

This project is a Flask-based web application that extracts frames from an uploaded video and uses a pre-trained TensorFlow model to detect fire in the frames. If fire is detected, a notification is sent via Telegram. The application is also containerized using Docker for easy deployment.

## Features

- Upload video files and extract frames at regular intervals.
- Use a pre-trained TensorFlow model to predict the presence of fire in each frame.
- Send a notification to a specified Telegram chat if fire is detected.
- Containerized using Docker for easy deployment and reproducibility.

## Workflow

1. **Upload Video**: Users can upload a video file through a simple web interface.
2. **Extract Frames**: The uploaded video is processed, and frames are extracted at regular intervals.
3. **Fire Detection**: Each extracted frame is analyzed using a TensorFlow model to detect the presence of fire.
4. **Telegram Notification**: If fire is detected in any frame, a message is sent to a specified Telegram chat.

## Screenshots

### Extracted Frames and Fire Detection
![Extracted Frames](https://firebasestorage.googleapis.com/v0/b/chat-api-aa04a.appspot.com/o/Screenshots%2F2024-07-18.png?alt=media&token=65b934c1-04ab-4a62-b945-207151a2c10d)

## Installation

### Prerequisites

- Docker
- Docker Compose

### Steps

1. Clone the repository:
    ```sh
    git clone https://github.com/afnamal/Fire-Detection
    cd Fire-Detection
    ```

2. Download the pre-trained model from Kaggle:
    - Visit the following Kaggle page to download the model: [Fire Detection Model](https://www.kaggle.com/code/jvkchaitanya410/fire-detection-using-resnet-50-accuracy-97/output)
    - Place the downloaded model file (`final_model.h5`) into the `prediction` directory.

3. Build and run the Docker containers:
    ```sh
    docker-compose up --build
    ```

4. The application will be available at:
    - `http://localhost:5001` for video upload
    - `http://localhost:5000` for fire detection
    - `http://localhost:15672` for RabbitMQ management interface (default credentials: `guest`/`guest`).

## API Endpoints

- **Upload Video**: `POST /upload_video`
    - Uploads a video file and starts the frame extraction process. 
    - Example using `curl`:
        ```sh
        curl -F "video=@path/to/your/video.ts" http://localhost:5001/upload_video
        ```

- **List Frames**: `GET /frames`
    - Returns a list of all extracted frames.

- **Get Frame**: `GET /frames/<filename>`
    - Retrieves a specific frame image.

- **Predict Fire**: `POST /predict`
    - Analyzes a given image for the presence of fire.
    - Example using `curl`:
        ```sh
        curl -F "image=@path/to/frame.jpg" http://localhost:5000/predict
        ```

## Usage

### Upload a Video

1. Open your browser and go to `http://localhost:5001`.
2. Use the interface to upload a `.ts` video file.
3. Frames will be extracted and analyzed for fire detection.

### Fire Detection

1. Once frames are extracted, they will be automatically analyzed.
2. If fire is detected in any frame, a message will be sent to the specified Telegram chat.

### Docker

This project uses Docker to ensure consistent environments and easy deployment. The `Dockerfile` and `docker-compose.yml` files are configured to set up the application with all necessary dependencies.

### RabbitMQ Management Interface

The RabbitMQ management interface is accessible at `http://localhost:15672` with the default credentials `guest`/`guest`. You can monitor the message queue and other RabbitMQ parameters from this interface.

## Project Structure

```plaintext
.
├── extraction             # Backend for frame extraction
│   ├── extrac_frames.py   # Frame extraction Flask application
│   ├── Dockerfile         # Docker configuration for frame extraction
│   └── requirements.txt   # Python dependencies for frame extraction
├── prediction             # Backend for fire prediction
│   ├── fire_detection.py  # Fire detection Flask application
│   ├── Dockerfile         # Docker configuration for fire detection
│   ├── final_model.h5     # Pre-trained model for fire detection (downloaded from Kaggle)
│   └── requirements.txt   # Python dependencies for fire detection
├── frontend               # Frontend Vue.js application
│   ├── app.vue            # Main Vue.js component
│   ├── Dockerfile         # Docker configuration for frontend
│   └── package.json       # JavaScript dependencies for frontend
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # This file

