# Node.js imajını kullanarak başlıyoruz
FROM node:14

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY package*.json ./
RUN npm install

# Uygulama kodunu kopyala
COPY . .

# .env dosyasını kopyala
COPY .env .env

# Ortam değişkenlerini yükle
ARG VUE_APP_EXTRACTION_API_URL
ARG VUE_APP_PREDICTION_API_URL
ENV VUE_APP_EXTRACTION_API_URL $VUE_APP_EXTRACTION_API_URL
ENV VUE_APP_PREDICTION_API_URL $VUE_APP_PREDICTION_API_URL

# Uygulamayı derle
RUN npm run build

# Uygulama portunu belirt
EXPOSE 8080

# Uygulamayı başlat
CMD ["npm", "run", "serve"]