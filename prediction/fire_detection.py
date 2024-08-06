from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io
import os
import requests
from dotenv import load_dotenv
import hashlib
import time
import pika

# Ortam değişkenlerini yükle
load_dotenv()

# Ortam değişkenini ayarla
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Model yolunu yazdır
model_path = "./final_model.h5"
print(f"Model path: {model_path}")

# Modeli yükle
model = None
try:
    model = load_model(model_path)
    model.summary()
except Exception as e:
    print(f"Model yüklenirken hata oluştu: {e}")

# Sayaç dosyasının yolunu belirle
counter_path = "/tmp/counter.txt"

detected_fire_hashes = set()
last_fire_time = 0
fire_reset_interval = 60  # Yangın resetleme aralığı (saniye)

def get_counter():
    """Sayaç dosyasını oku veya oluştur ve sayaç değerini döndür"""
    if not os.path.exists(counter_path):
        with open(counter_path, 'w') as f:
            f.write('0')
    with open(counter_path, 'r') as f:
        count = int(f.read().strip())
    with open(counter_path, 'w') as f:
        f.write(str(count + 1))
    return count

def preprocess_image(image):
    """Resmi ön işleme"""
    image = image.resize((300, 300))
    image = np.array(image)
    if image.shape[-1] == 4:  # RGBA görüntüler için alfa kanalını çıkarın
        image = image[..., :3]
    image = np.expand_dims(image, axis=0)
    return image

def get_image_hash(image):
    """Resmin hash değerini hesapla"""
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='JPEG')
    image_bytes = image_bytes.getvalue()
    return hashlib.md5(image_bytes).hexdigest()

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

def predict_fire(image):
    """Resimde yangın olup olmadığını tahmin etme ve hash kontrolü yapma"""
    global last_fire_time
    current_time = time.time()

    # Eğer belirli bir süre geçmişse hash setini temizle
    if current_time - last_fire_time > fire_reset_interval:
        detected_fire_hashes.clear()

    if is_corrupted_or_gray(image):
        return ("gray", 0, False)

    processed_image = preprocess_image(image)
    predictions = model.predict(processed_image)
    fire_prob = predictions[0][0]
    if fire_prob >= 0.5:
        image_hash = get_image_hash(image)
        if image_hash in detected_fire_hashes:
            return ("fire", fire_prob, False)
        else:
            detected_fire_hashes.add(image_hash)
            last_fire_time = current_time
            return ("fire", fire_prob, True)
    return ("no fire", fire_prob, False)

def send_telegram_message(message, image_path):
    """Telegram botuna mesaj gönderme"""
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    print(f"Bot token: {bot_token}")
    print(f"Chat ID: {chat_id}")
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    telegram_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    try:
        response = requests.post(telegram_url, data={
            'chat_id': chat_id,
            'text': message,
        })
        if response.status_code != 200:
            print(f"Telegram mesaj gönderilemedi: {response.text}")
            return False

        with open(image_path, 'rb') as image_file:
            response = requests.post(telegram_photo_url, data={
                'chat_id': chat_id,
            }, files={'photo': image_file})
            if response.status_code != 200:
                print(f"Telegram fotoğraf gönderilemedi: {response.text}")
                return False
        
        return True
    except Exception as e:
        print(f"Telegram mesaj gönderilemedi: {e}")
        return False

app = Flask(__name__)
CORS(app)

# RabbitMQ bağlantısı
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue='frame_queue')

def callback(ch, method, properties, body):
    """Kuyruktan gelen mesajları işleyin"""
    try:
        image = Image.open(io.BytesIO(body))
        timestamp = properties.headers['timestamp']
        prediction_class, prediction_prob, is_new_detection = predict_fire(image)
        print(f"{timestamp} - Tahmin: {prediction_class}, Olasılık: {prediction_prob:.2f}")
        
        if prediction_class == "fire" and is_new_detection:
            message = f"Yangın Tespit Edildi! Olasılık: {prediction_prob:.2f}"
            count = get_counter()
            image_path = f"/tmp/detected_fire_{count}.jpg"
            image.save(image_path)
            send_telegram_message(message, image_path)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Hata: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='frame_queue', on_message_callback=callback)

print(" [*] Kuyruk dinleniyor. Çıkmak için CTRL+C tuşlayın.")
channel.start_consuming()

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model yüklenemedi'}), 500
    
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No image uploaded'}), 400

    try:
        image = Image.open(io.BytesIO(file.read()))
        prediction_class, prediction_prob, is_new_detection = predict_fire(image)

        if prediction_class == "fire" and is_new_detection:
            message = f"Yangın Tespit Edildi! Olasılık: {prediction_prob:.2f}"
            count = get_counter()
            image_path = f"/tmp/detected_fire_{count}.jpg"
            image.save(image_path)
            send_telegram_message(message, image_path)

        return jsonify({'predicted_class': prediction_class, 'probability': float(prediction_prob)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
