from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import pika

# Ortam değişkenlerini yükle
load_dotenv()

app = Flask(__name__)
CORS(app)

# RabbitMQ bağlantısı
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue='telegram_queue')

def send_telegram_message(chat_id, bot_token, message, image_path):
    """Telegram botuna mesaj gönderme"""
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

        if image_path:
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

def callback(ch, method, properties, body):
    """Kuyruktan gelen mesajları işleyin"""
    try:
        message_data = eval(body.decode())
        chat_id = message_data['chat_id']
        bot_token = message_data['bot_token']
        message = message_data['message']
        image_path = message_data.get('image_path', None)
        success = send_telegram_message(chat_id, bot_token, message, image_path)
        
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_nack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Hata: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='telegram_queue', on_message_callback=callback)

print(" [*] Kuyruk dinleniyor. Çıkmak için CTRL+C tuşlayın.")
channel.start_consuming()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
