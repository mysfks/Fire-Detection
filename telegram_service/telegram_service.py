import os
import pika
import requests
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

# RabbitMQ bağlantısı
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'guest')
credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='telegram_queue')

def send_telegram_message(bot_token, chat_id, message, image_path):
    try:
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        telegram_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        response = requests.post(telegram_url, data={'chat_id': chat_id, 'text': message})
        if response.status_code != 200:
            print(f"Telegram mesaj gönderilemedi: {response.text}")
            return False

        with open(image_path, 'rb') as image_file:
            response = requests.post(telegram_photo_url, data={'chat_id': chat_id}, files={'photo': image_file})
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
        message_data = json.loads(body)
        bot_token = message_data['bot_token']
        chat_id = message_data['chat_id']
        message = message_data['message']
        image_path = message_data['image_path']
        send_telegram_message(bot_token, chat_id, message, image_path)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Hata: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='telegram_queue', on_message_callback=callback)

print(" [*] Telegram kuyruk dinleniyor. Çıkmak için CTRL+C tuşlayın.")
channel.start_consuming()
