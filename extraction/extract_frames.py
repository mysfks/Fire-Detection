import os
import time
import cv2
import pika
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
from datetime import datetime
from dotenv import load_dotenv
import shutil
import requests
import numpy as np
from PIL import Image
import io
import hashlib

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
CORS(app)

# Geçici olarak kaydedilecek karelerin yolu
output_folder = "frames"
fire_detected_folder = "fire_detected_frames"
completion_flag = os.path.join(output_folder, "extraction_complete.txt")
log_file_path = "logs.txt"

# Çıktı klasörlerini oluştur
for folder in [output_folder, fire_detected_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# RTSP URL bilgilerini .env dosyasından al
rtsp_user = os.getenv("RTSP_USER")
rtsp_password = os.getenv("RTSP_PASSWORD")
rtsp_ip = os.getenv("RTSP_IP")
rtsp_port = os.getenv("RTSP_PORT")
rtsp_path = os.getenv("RTSP_PATH")
rtsp_url = f'rtsp://{rtsp_user}:{rtsp_password}@{rtsp_ip}:{rtsp_port}/{rtsp_path}'

capture_interval = 20  # Varsayılan kare alma aralığı
interval_lock = threading.Lock()

telegram_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

# RabbitMQ bağlantısı
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'guest')
credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='frame_queue')

detected_fire_hashes = set()

def send_telegram_message(message, image_path):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendPhoto",
                data={"chat_id": chat_id},
                files={"photo": image_file}
            )
            return response.status_code == 200
    return False

def get_image_hash(image):
    """Resmin hash değerini hesapla"""
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='JPEG')
    image_bytes = image_bytes.getvalue()
    return hashlib.md5(image_bytes).hexdigest()

def clear_old_frames():
    """Karelerin kaydedildiği klasörü temizle"""
    now = time.time()
    cutoff = now - 3 * 60  # 3 dakika öncesi
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff:
                os.remove(file_path)

def is_corrupted_or_gray(image):
    """Resmin bozuk veya gri tonlamalı olup olmadığını kontrol et"""
    if image.mode not in ("L", "RGB"):
        return False

    if image.mode == "RGB":
        gray_image = image.convert('L')
        histogram = gray_image.histogram()
        total_pixels = sum(histogram)
        if total_pixels == 0:
            return True
        gray_level_distribution = [float(count) / total_pixels for count in histogram]
        max_gray_level = max(gray_level_distribution)
        if max_gray_level > 0.9:
            return True
    return False

def capture_image_from_stream():
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        log_message("Kamera bağlantısı kurulamadı.")
        return

    ret, frame = cap.read()
    if ret:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if is_corrupted_or_gray(image):
            log_message("Bozuk veya gri tonlamalı görüntü atlandı.")
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        img_name = f"image_{timestamp}.jpg"
        img_path = os.path.join(output_folder, img_name)
        image.save(img_path)
        os.chmod(img_path, 0o777)  # Dosyaya tam izin ver
        log_message(f"{img_name} kaydedildi.")

        # RabbitMQ'ya görüntüyü gönder
        _, buffer = cv2.imencode('.jpg', frame)
        channel.basic_publish(exchange='',
                              routing_key='frame_queue',
                              body=buffer.tobytes(),
                              properties=pika.BasicProperties(
                                  headers={'timestamp': timestamp}
                              ))
        log_message(f"{timestamp} - Kare RabbitMQ'ya gönderildi.")
    else:
        log_message("Görüntü alınamadı.")
    cap.release()

def capture_images_periodically():
    global capture_interval
    while True:
        with interval_lock:
            interval = capture_interval
        capture_image_from_stream()
        clear_old_frames()
        for _ in range(interval):
            time.sleep(1)
            with interval_lock:
                new_interval = capture_interval
                if new_interval != interval:
                    break

@app.route('/frames', methods=['GET'])
def list_frames():
    try:
        files = os.listdir(output_folder)
        files.sort(key=lambda f: os.path.getmtime(os.path.join(output_folder, f)))
        return jsonify(files), 200
    except Exception as e:
        log_message(f"Error listing frames: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/frames/<filename>', methods=['GET'])
def get_frame(filename):
    return send_from_directory(output_folder, filename)

@app.route('/set_interval', methods=['POST'])
def set_interval():
    global capture_interval
    try:
        data = request.get_json()
        interval = data.get('interval')
        log_message(f"Received interval: {interval}")
        if interval and isinstance(interval, int) and interval > 0:
            with interval_lock:
                capture_interval = interval
            log_message(f"Updated capture interval to: {capture_interval}")
            return jsonify({'message': 'Interval updated successfully.'}), 200
        else:
            log_message("Invalid interval value received.")
            return jsonify({'error': 'Invalid interval value.'}), 400
    except Exception as e:
        log_message(f"Error setting interval: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        if not os.path.exists(log_file_path):
            return jsonify({'error': 'Log dosyası bulunamadı.'}), 404

        with open(log_file_path, 'r') as log_file:
            logs = log_file.readlines()

        return jsonify(logs), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def log_message(message):
    """Log dosyasına mesaj yaz"""
    with open(log_file_path, 'a') as log_file:
        log_file.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}\n')

if __name__ == '__main__':
    # Kare çıkarma iş parçacığını başlat
    thread = threading.Thread(target=capture_images_periodically)
    thread.start()
    app.run(debug=True, host='0.0.0.0', port=5001)
