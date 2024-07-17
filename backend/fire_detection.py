from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import io
import os
import requests

# Ortam değişkenini ayarla
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Modeli yükle
model_path = "./final_model.h5"  # İndirilen modelin yolu
model = None
try:
    model = load_model(model_path)
    model.summary()  # Modelin yapısını çıktıya ver
except Exception as e:
    print(f"Model yüklenirken hata oluştu: {e}")

def preprocess_image(image):
    """Resmi ön işleme"""
    image = image.resize((300, 300))  # Modelinizin beklediği giriş boyutuna göre ayarlayın
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

def send_telegram_message(message):
    """Telegram botuna mesaj gönderme"""
    bot_token = '7320273980:AAE0PUg-wC0DkYUiuQpBjxaqs4DV36hR2co'
    chat_id = '1010415776'
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        response = requests.post(telegram_url, data={
            'chat_id': chat_id,
            'text': message,
        })
        return response.status_code == 200
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
            send_telegram_message(message)

        return jsonify({'predicted_class': prediction_class, 'probability': float(prediction_prob)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
