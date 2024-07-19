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
    git clone https://github.com/yourusername/video-fire-detection.git
    cd video-fire-detection
    ```

2. Build and run the Docker containers:
    ```sh
    docker-compose up --build
    ```

   **Note**: During the Docker build process, the `final_model.h5` file will be automatically downloaded from the following link:
   [Download Model](https://www.kaggleusercontent.com/kf/117604734/eyJhbGciOiJkaXIiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2In0..W9KC660iyogH7sUxFkdRlQ.tckruepxOxc0F6DGM6gqb7qdqxjlwepbfOxyRCNH5nKJ0-T-UvFYwMyi22dP7ko1GjuXUX7UkyRaMyg4JR2DxWbK2WiP2sQrR2iIxPoYYusu45yQdaRwbelbjchYWm9-EBPGhQXd5Cra8cdJEHItWFKHOWzxU6vTanSVTT5avpqVbcOgEEA_cZxCnX3sjJCxuHfLCmKPCFLYhJyU6oYdyEdOVBZV9pRSbXByw6KZNDpES5OrVCRDOD1DQAN2x83XngwrjrOZfdZGjDi2odFeNrRMFUTpXnmdner9zFfGavnRyHFu25fxAriyWsgF1fBHaX_jukgzBdwKo8L2hnuddyJikVY6z8tHdA6CzyiA1KmhPhW22OWo_BuaEb06bsai69y71EJpU61ptxd2n-9lRm7FLHOa-T2vhrRr2SBL7qGnGcnAEiL8sWPrdtGTDlqqWeXJKZnnXhUHs1mb_XSJ71mUHo23UDSPAHMWep_zUTkzJR751oePDucc8ed18NNJv7JJz0cwJFFY7DAhPgZQUp32EeuIUJVqv6DXzuR6X-EMci0TwxQyJpGUxXhdiCo7aXBPj4u2a1Ztt_TBkSi30BCzzjuW3V6C-kj11kN2L_au5vlK92u9qgz_Tx7wMcwG981WVll25UvXEoXFePj9FS0e1ocgu4pK2mXbG3wHNtc.uTmzotaHMPeYYiUNaKDJ7g/final_model.h5).

3. The application will be available at `http://localhost:5001` for video upload and `http://localhost:5000` for fire detection.


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
│   └── requirements.txt   # Python dependencies for fire detection
├── frontend               # Frontend Vue.js application
│   ├── app.vue            # Main Vue.js component
│   ├── Dockerfile         # Docker configuration for frontend
│   └── package.json       # JavaScript dependencies for frontend
├── docker-compose.yml     # Docker Compose configuration
├── final_model.h5         # Pre-trained model for fire detection
└── README.md              # This file
```

## Acknowledgements

- The pre-trained fire detection model used in this project can be downloaded from [Kaggle](https://www.kaggle.com/code/jvkchaitanya410/fire-detection-using-resnet-50-accuracy-97/output).

---

By following these steps and using the provided endpoints, you can effectively upload videos, extract frames, detect fire, and receive notifications via Telegram.

If you encounter any issues or have questions, please feel free to open an issue on the repository.
