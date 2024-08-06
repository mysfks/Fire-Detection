from flask import Flask, send_file, jsonify
from pymongo import MongoClient
from gridfs import GridFS
import io
from dotenv import load_dotenv
import os

# Ortam değişkenlerini yükle
load_dotenv()

app = Flask(__name__)

# MongoDB bağlantısı
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', 27017))

client = MongoClient(f'mongodb://{mongo_host}:{mongo_port}/')
db = client['mydatabase']
fs = GridFS(db)

@app.route('/photos', methods=['GET'])
def list_photos():
    """Tüm fotoğrafların listesini döndür."""
    file_list = fs.list()
    return jsonify(file_list)

@app.route('/photos/<filename>', methods=['GET'])
def get_photo(filename):
    """Belirli bir fotoğrafı döndür."""
    try:
        grid_out = fs.get_last_version(filename=filename)
        image_data = grid_out.read()
        return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
    except Exception as e:
        return str(e), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
