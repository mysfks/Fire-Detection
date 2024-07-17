# Temel imaj olarak Node.js kullan
FROM node:14

# Çalışma dizinini ayarla
WORKDIR /app

# package.json ve yarn.lock dosyalarını kopyala
COPY package.json yarn.lock ./

# Bağımlılıkları yükle
RUN yarn install

# Uygulama dosyalarını kopyala
COPY . .

# Uygulamayı derle
RUN yarn build

# Uygulamanın servis portunu ayarla
EXPOSE 8080

# Uygulamayı başlat
CMD ["yarn", "serve"]
