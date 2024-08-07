# Temel imaj olarak Python 3.9 kullan
FROM python:3.8

# Çalışma dizinini ayarla
WORKDIR /app

# Gereksinim dosyalarını kopyala
COPY requirements.txt .

# Gereksinimleri yükle
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# MongoDB'ye bağlanabilmek için varsayılan portu aç
EXPOSE 27017

# Docker konteyneri başlatıldığında çalışacak komutu belirt
CMD ["python", "mongo_uploader.py"]