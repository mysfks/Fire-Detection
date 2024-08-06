from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
import base64
import os

# Ortam değişkenlerini yükle
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB bağlantısı
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client['mydatabase']
fs = GridFS(db)

@app.route('/api/photos', methods=['GET'])
def get_photos():
    photos = []
    for grid_out in fs.find():
        photo = {
            "filename": grid_out.filename,
            "data": base64.b64encode(grid_out.read()).decode('utf-8'),
            "uploadDate": grid_out.upload_date
        }
        photos.append(photo)
    return jsonify(photos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
