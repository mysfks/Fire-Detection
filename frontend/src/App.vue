<template>
  <div id="app" class="container mt-5">
    <h1 class="text-center mb-4">Video Kare Çıkarıcı ve Yangın Tespiti</h1>
    <div class="upload-section text-center mb-4">
      <div class="custom-file mb-3">
        <input type="file" @change="onFileChange" accept=".ts,video/*" class="custom-file-input" id="customFile" />
        <label class="custom-file-label" for="customFile">{{ videoFile ? videoFile.name : 'Video dosyası seçin (TS dahil)' }}</label>
      </div>
      <button @click="uploadVideo" class="btn btn-primary">Videoyu Yükle</button>
    </div>
    <div v-if="successMessage" class="alert alert-success text-center">
      <p>{{ successMessage }}</p>
    </div>
    <div v-if="errorMessage" class="alert alert-danger text-center">
      <p>{{ errorMessage }}</p>
    </div>
    <div v-if="frames.length" class="frames-section">
      <h2 class="text-center mb-4">Çıkarılan Kareler</h2>
      <div class="row">
        <div v-for="(frame, index) in frames" :key="index" class="col-md-4 mb-4">
          <div class="card" :class="{'fire-alarm': frame.prediction?.predicted_class === 'fire', 'no-fire': frame.prediction?.predicted_class === 'no fire'}">
            <img :src="frame.url" class="card-img-top" :alt="'Kare ' + (index + 1)" />
            <div v-if="frame.prediction" class="card-body">
              <h5 class="card-title">Tahmin Edilen Sınıf: {{ frame.prediction.predicted_class }}</h5>
              <p class="card-text">Olasılık: {{ frame.prediction.probability }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      videoFile: null,
      successMessage: '',
      errorMessage: '',
      frames: [],
      loading: false,
      intervalId: null,  // interval ID'yi sakla
    };
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.videoFile = file;
      }
    },
    async uploadVideo() {
      if (!this.videoFile) {
        alert("Lütfen önce bir video dosyası seçin.");
        return;
      }

      const formData = new FormData();
      formData.append('video', this.videoFile);

      try {
        this.loading = true;
        this.frames = [];  // Önceki kareleri temizle
        this.clearCheckFramesInterval();  // Önceki interval'i temizle
        await axios.post('http://127.0.0.1:5001/upload_video', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        this.errorMessage = '';
        this.successMessage = 'Video başarıyla yüklendi ve kareler çıkarılıyor.';
        this.checkFrames();  // Kareleri kontrol etmeye başla
      } catch (error) {
        this.successMessage = '';
        this.errorMessage = error.response ? error.response.data : error.message;
      }
    },
    clearCheckFramesInterval() {
      if (this.intervalId) {
        clearInterval(this.intervalId);
        this.intervalId = null;
      }
    },
    async checkFrames() {
      // Karelerin çıkarılmasına izin vermek için belirli aralıklarla kontrol et
      this.intervalId = setInterval(async () => {
        try {
          const response = await axios.get('http://127.0.0.1:5001/frames');
          if (response.status === 200) {
            this.frames = response.data.map((frame) => ({
              url: `http://127.0.0.1:5001/frames/${frame}`,
              prediction: null,
            }));
            this.clearCheckFramesInterval();  // Tüm kareler çıkarıldıktan sonra kontrolü durdur
            this.frames.forEach(frame => {
              this.predictFire(frame);
            });
          } else if (response.status === 202) {
            console.log('Kare çıkarma işlemi devam ediyor...');
          }
        } catch (error) {
          this.errorMessage = error.response ? error.response.data : error.message;
        }
      }, 3000);  // 3 saniye aralıklarla kontrol et
    },
    async predictFire(frame) {
      try {
        const formData = new FormData();
        const response = await axios.get(frame.url, { responseType: 'blob' });
        formData.append('image', response.data, 'frame.jpg');
        const predictionResponse = await axios.post('http://127.0.0.1:5000/predict', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        frame.prediction = predictionResponse.data;
      } catch (error) {
        this.errorMessage = error.response ? error.response.data : error.message;
      }
    },
  },
  beforeUnmount() {
    this.clearCheckFramesInterval();  // Bileşen yok edildiğinde interval'i temizle
  }
};
</script>

<style>
.container {
  max-width: 800px;
  margin: 0 auto;
}

.card.fire-alarm {
  border-color: red;
  animation: blink 1s infinite;
}

.card.no-fire {
  border-color: green;
}

.alert {
  margin-top: 20px;
}

.custom-file-input ~ .custom-file-label::after {
  content: "Gözat";
}

@keyframes blink {
  0% {
    border-color: red;
  }
  50% {
    border-color: yellow;
  }
  100% {
    border-color: red;
  }
}
</style>
