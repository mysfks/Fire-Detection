from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io
import os
import hashlib
import time
import pika
from dotenv import load_dotenv
import json

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

app = Flask(__name__)
CORS(app)

# RabbitMQ bağlantısı
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'guest')
credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='frame_queue')
channel.queue_declare(queue='telegram_queue')

fire_detected_folder = '../extraction/fire_detected_frames'

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
            image_path = os.path.join(fire_detected_folder, f"detected_fire_{count}.jpg")
            image.save(image_path)
            # Telegram mesajı için RabbitMQ'ya mesaj gönder
            telegram_message = {
                'chat_id': os.getenv('CHAT_ID'),
                'bot_token': os.getenv('BOT_TOKEN'),
                'message': message,
                'image_path': image_path
            }
            channel.basic_publish(exchange='',
                                  routing_key='telegram_queue',
                                  body=json.dumps(telegram_message))

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
            image_path = os.path.join(fire_detected_folder, f"detected_fire_{count}.jpg")
            image.save(image_path)
            # Telegram mesajı için RabbitMQ'ya mesaj gönder
            telegram_message = {
                'chat_id': os.getenv('CHAT_ID'),
                'bot_token': os.getenv('BOT_TOKEN'),
                'message': message,
                'image_path': image_path
            }
            channel.basic_publish(exchange='',
                                  routing_key='telegram_queue',
                                  body=json.dumps(telegram_message))

        return jsonify({'predicted_class': prediction_class, 'probability': float(prediction_prob)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
