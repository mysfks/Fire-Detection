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

def predict_fire(image):
    """Resimde yangın olup olmadığını tahmin etme"""
    processed_image = preprocess_image(image)
    predictions = model.predict(processed_image)
    fire_prob = predictions[0][0]
    return ("fire", fire_prob) if fire_prob >= 0.5 else ("no fire", 1 - fire_prob)

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

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model yüklenemedi'}), 500
    
    file = request.files.get('image')
    if not file:
        return jsonify({'error': 'No image uploaded'}), 400

    try:
        image = Image.open(io.BytesIO(file.read()))
        prediction_class, prediction_prob = predict_fire(image)

        if prediction_class == "fire":
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
