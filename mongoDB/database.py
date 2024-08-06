import os
from pymongo import MongoClient
from gridfs import GridFS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Ortam değişkenlerini yükle
load_dotenv()

class PhotoHandler(FileSystemEventHandler):
    def __init__(self, db):
        self.fs = GridFS(db)

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return
        
        file_path = event.src_path
        print(f"Yeni fotoğraf bulundu: {file_path}")

        try:
            with open(file_path, 'rb') as photo_file:
                file_id = self.fs.put(photo_file, filename=os.path.basename(file_path))
                print(f"Fotoğraf MongoDB'ye kaydedildi, dosya ID: {file_id}")
        except Exception as e:
            print(f"Bir hata oluştu: {e}")

# MongoDB Atlas bağlantı dizesini ortam değişkenlerinden al
mongo_uri = os.getenv('MONGO_URI')

# MongoDB Atlas'a bağlan
client = MongoClient(mongo_uri)
db = client['mydatabase']

photos_directory = '../extraction/fire_detected_frames'

event_handler = PhotoHandler(db)
observer = Observer()
observer.schedule(event_handler, path=photos_directory, recursive=False)

observer.start()
print(f"{photos_directory} dizini izleniyor. Çıkmak için Ctrl+C basın.")

try:
    while True:
        pass  
except KeyboardInterrupt:
    observer.stop()

observer.join()
