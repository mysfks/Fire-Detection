<template>
  <div id="app" class="container mt-5">
    <h1 class="text-center mb-4">Video Kare Çıkarıcı ve Yangın Tespiti</h1>
    <div v-if="successMessage" class="alert alert-success text-center">
      <p>{{ successMessage }}</p>
    </div>
    <div v-if="errorMessage" class="alert alert-danger text-center">
      <p>{{ errorMessage }}</p>
    </div>
    <div class="mb-4 text-center">
      <label for="interval-input" class="form-label">Kaç saniyede bir kare alınsın?</label>
      <div class="input-group w-50 mx-auto">
        <input type="number" id="interval-input" v-model.number="interval" class="form-control" min="1" />
        <button class="btn btn-primary" @click="setCaptureInterval">Güncelle</button>
      </div>
    </div>
    <div class="mb-4 text-center">
      <div class="status-box">
        <p><strong>Son Kontrol Zamanı:</strong> {{ lastCheckedTime }}</p>
        <p><strong>Durum:</strong> {{ currentStatus }}</p>
      </div>
    </div>
    <div v-if="filteredFrames.length" class="frames-section">
      <h2 class="text-center mb-4">Çıkarılan Kareler</h2>
      <div class="row">
        <div v-for="(frame, index) in filteredFrames" :key="index" class="col-12 mb-4">
          <div :class="['card', getRiskClass(frame.prediction), 'shadow-sm', 'p-3', 'mb-5', 'bg-white', 'rounded']">
            <a :href="frame.url" target="_blank" rel="noopener noreferrer">
              <img :src="frame.url" class="card-img-top" :alt="'Kare ' + (index + 1)" />
            </a>
            <div class="card-body">
              <h5 class="card-title">Görüntü Zamanı: {{ formatTimestamp(frame.timestamp) }}</h5>
              <p class="card-text">IP Adresi: {{ rtspIp }}</p>
              <div v-if="frame.prediction">
                <h5 class="card-title">Tahmin Edilen Sınıf: {{ frame.prediction.predicted_class }}</h5>
                <p class="card-text">Olasılık: {{ formatProbability(frame.prediction.probability) }}</p>
                <p class="card-text">{{ getRiskLevel(frame.prediction) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="terminal">
      <h2 class="text-center mb-4">Log</h2>
      <pre class="logInside">{{ logs.join('\n') }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';

export default {
  setup() {
    const successMessage = ref('');
    const errorMessage = ref('');
    const frames = ref([]);
    const interval = ref(20);
    const intervalId = ref(null);
    const isPredicting = ref(false);
    const lastCheckedTime = ref('');
    const currentStatus = ref('No Fire');
    const logs = ref([]);

    const rtspIp = process.env.VUE_APP_RTSP_IP;

    const setCaptureInterval = async () => {
      try {
        const response = await axios.post(`${process.env.VUE_APP_EXTRACTION_API_URL}/set_interval`, { interval: interval.value });
        successMessage.value = response.data.message;
        errorMessage.value = '';
        addLog(`Interval set to: ${interval.value}`);
      } catch (error) {
        errorMessage.value = error.response ? error.response.data.error : error.message;
        successMessage.value = '';
        addLog(`Error setting interval: ${error.message}`);
      }
    };

    const clearCheckFramesInterval = () => {
      if (intervalId.value) {
        clearInterval(intervalId.value);
        intervalId.value = null;
      }
    };

    const startCapturingFrames = () => {
      clearCheckFramesInterval();
      checkFrames();
      intervalId.value = setInterval(checkFrames, 5000);
    };

    const checkFrames = async () => {
      try {
        const response = await axios.get(`${process.env.VUE_APP_EXTRACTION_API_URL}/frames`);
        lastCheckedTime.value = new Date().toLocaleString();
        addLog(`Checked frames at: ${lastCheckedTime.value}`);
        if (response.status === 200) {
          frames.value = response.data.map((frame) => ({
            url: `${process.env.VUE_APP_EXTRACTION_API_URL}/frames/${frame}`,
            prediction: null,
            timestamp: frame.split('_')[1].split('.')[0],
            ip: rtspIp
          })).reverse();
          isPredicting.value = true;
          for (let frame of frames.value) {
            if (!frame.prediction) {
              await predictFire(frame);
            }
          }
          isPredicting.value = false;
          currentStatus.value = frames.value.some(frame => frame.prediction && frame.prediction.probability >= 0.5) ? 'Fire Detected' : 'No Fire';
          addLog(`Current status: ${currentStatus.value}`);
        } else if (response.status === 202) {
          addLog('Frame extraction in progress...');
        }
      } catch (error) {
        errorMessage.value = error.response ? error.response.data : error.message;
        addLog(`Error checking frames: ${error.message}`);
      }
    };

    const predictFire = async (frame) => {
      if (frame.prediction) return;

      try {
        const formData = new FormData();
        const response = await axios.get(frame.url, { responseType: 'blob' });
        formData.append('image', response.data, 'frame.jpg');
        const predictionResponse = await axios.post(`${process.env.VUE_APP_PREDICTION_API_URL}/predict`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        frame.prediction = predictionResponse.data;
        addLog(`Prediction for frame ${frame.url}: ${frame.prediction.predicted_class} with probability ${frame.prediction.probability}`);
      } catch (error) {
        errorMessage.value = error.response ? error.response.data : error.message;
        addLog(`Error predicting fire for frame ${frame.url}: ${error.message}`);
      }
    };

    const getRiskClass = (prediction) => {
      if (!prediction) return '';
      const probability = prediction.probability;
      if (probability >= 0.9) return 'very-high-risk';
      if (probability >= 0.7) return 'high-risk';
      if (probability >= 0.5) return 'risky';
      return 'no-fire';
    };

    const getRiskLevel = (prediction) => {
      if (!prediction) return '';
      const probability = prediction.probability;
      if (probability >= 0.9) return 'Çok Yüksek Risk';
      if (probability >= 0.7) return 'Yüksek Risk';
      if (probability >= 0.5) return 'Riskli';
      return 'Yangın Yok';
    };

    const formatProbability = (probability) => {
      return (probability * 100).toFixed(2) + '%';
    };

    const formatTimestamp = (timestamp) => {
      const date = new Date(`${timestamp.slice(0, 4)}-${timestamp.slice(4, 6)}-${timestamp.slice(6, 8)}T${timestamp.slice(9, 11)}:${timestamp.slice(11, 13)}:${timestamp.slice(13, 15)}`);
      return date.toLocaleString();
    };

    const filteredFrames = computed(() => {
      return frames.value.filter(frame => frame.prediction && frame.prediction.probability >= 0.5);
    });

    const addLog = (message) => {
      logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${message}`);
      if (logs.value.length > 100) {
        logs.value.pop();
      }
    };

    onMounted(() => {
      startCapturingFrames();
    });

    onBeforeUnmount(() => {
      clearCheckFramesInterval();
    });

    return {
      successMessage,
      errorMessage,
      frames,
      interval,
      setCaptureInterval,
      getRiskClass,
      getRiskLevel,
      formatProbability,
      formatTimestamp,
      rtspIp,
      filteredFrames,
      lastCheckedTime,
      currentStatus,
      logs
    };
  }
};
</script>

<style>
.card.very-high-risk {
  border-color: red;
  background-color: rgba(255, 0, 0, 0.1);
  color: red;
}

.card.high-risk {
  border-color: orange;
  background-color: rgba(255, 165, 0, 0.1);
  color: orange;
}

.card.risky {
  border-color: yellow;
  background-color: rgba(255, 255, 0, 0.1);
  color: yellow;
}

.card.no-fire {
  border-color: green;
}

.card.fire-alarm {
  border-color: red;
  animation: blink 1s infinite;
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.alert {
  margin-top: 20px;
}

.card {
  transition: all 0.3s ease-in-out;
}

.card:hover {
  transform: scale(1.05);
}

.status-box {
  border: 1px solid #ddd;
  padding: 10px;
  display: inline-block;
  border-radius: 5px;
}

.terminal {
  background-color: #2c2525;
  color: #0f0;
  padding: 10px;
  height: 200px;
  overflow-y: scroll;
  margin-top: 20px;
  border-radius: 5px;
}

.terminal pre {
  margin: 0;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.4;
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
.logInside{
  color: rgb(142, 143, 143);
}
</style>
