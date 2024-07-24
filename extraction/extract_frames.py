import os
import time
import cv2
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
from datetime import datetime
from dotenv import load_dotenv
import shutil
import requests

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
CORS(app)

# Geçici olarak kaydedilecek karelerin yolu
output_folder = "frames"
fire_detected_folder = "fire_detected"
completion_flag = os.path.join(output_folder, "extraction_complete.txt")

# Çıktı klasörlerini oluştur
for folder in [output_folder, fire_detected_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# RTSP URL'nizi buraya girin (kullanıcı adı, şifre ve IP adresini doğru bir şekilde belirtin)
rtsp_url = 'rtsp://erpstajyer:YYQy;LJ7l0@10.0.66.195:554/Streaming/Channels/101'

capture_interval = 20  # Varsayılan kare alma aralığı
interval_lock = threading.Lock()

telegram_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

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

def capture_image_from_stream():
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("Kamera bağlantısı kurulamadı.")
        return
    
    ret, frame = cap.read()
    if ret:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        img_name = f'image_{timestamp}.jpg'
        img_path = os.path.join(output_folder, img_name)
        cv2.imwrite(img_path, frame)
        os.chmod(img_path, 0o777)  # Dosyaya tam izin ver
        print(f'{img_name} kaydedildi.')
    else:
        print("Görüntü alınamadı.")
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
        print(f"Received interval: {interval}")
        if interval and isinstance(interval, int) and interval > 0:
            with interval_lock:
                capture_interval = interval
            print(f"Updated capture interval to: {capture_interval}")
            return jsonify({'message': 'Interval updated successfully.'}), 200
        else:
            print("Invalid interval value received.")
            return jsonify({'error': 'Invalid interval value.'}), 400
    except Exception as e:
        print(f"Error setting interval: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    # Tahmin işlemleri burada gerçekleştirilir
    # Tahmin edilen sonuç yangınsa, görüntü fire_detected klasörüne kopyalanır
    # Örneğin, tahmin sonucunu 'fire_detected' değişkeni olarak alalım
    fire_detected = False  # Bu, tahmin sonuçlarına göre belirlenir
    
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No image uploaded'}), 400
    
    # Görüntüyü kaydet
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    img_name = f'image_{timestamp}.jpg'
    img_path = os.path.join(output_folder, img_name)
    file.save(img_path)
    
    if fire_detected:
        fire_img_path = os.path.join(fire_detected_folder, img_name)
        shutil.copy(img_path, fire_img_path)
        os.chmod(fire_img_path, 0o777)
        print(f'{img_name} yangın tespit edildi ve {fire_detected_folder} klasörüne kaydedildi.')

        # Telegram mesajı gönder
        risk_level = 'Çok Yüksek Risk' if fire_detected else 'Yangın Yok'
        message = f"Kamera IP: {rtsp_url}\nZaman: {timestamp}\nRisk Seviyesi: {risk_level}"
        send_telegram_message(message)
    
    return jsonify({'message': 'Prediction completed.'}), 200

if __name__ == '__main__':
    # Kare çıkarma iş parçacığını başlat
    thread = threading.Thread(target=capture_images_periodically)
    thread.start()
    app.run(debug=True, host='0.0.0.0', port=5001)
