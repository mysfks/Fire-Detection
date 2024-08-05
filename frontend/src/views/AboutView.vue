<template>
  <div class="container mt-5">
    <h1 class="text-center mb-4">Yakalanan Yangın Kareleri</h1>
    <div v-if="filteredFrames.length" class="frames-section">
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
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted, computed } from 'vue'

export default {
  setup() {
    const frames = ref([])
    const isPredicting = ref(false)
    const lastCheckedTime = ref('')
    const currentStatus = ref('No Fire')
    const rtspIp = process.env.VUE_APP_RTSP_IP

    const checkFrames = async () => {
      try {
        const response = await axios.get(`${process.env.VUE_APP_EXTRACTION_API_URL}/frames`)
        lastCheckedTime.value = new Date().toLocaleString()
        if (response.status === 200) {
          frames.value = response.data.map((frame) => ({
            url: `${process.env.VUE_APP_EXTRACTION_API_URL}/frames/${frame}`,
            prediction: null,
            timestamp: frame.split('_')[1].split('.')[0],
            ip: rtspIp
          })).reverse()
          isPredicting.value = true
          for (let frame of frames.value) {
            if (!frame.prediction) {
              await predictFire(frame)
            }
          }
          isPredicting.value = false
          currentStatus.value = frames.value.some(frame => frame.prediction && frame.prediction.probability >= 0.5) ? 'Fire Detected' : 'No Fire'
        }
      } catch (error) {
        console.error(error)
      }
    }

    const predictFire = async (frame) => {
      if (frame.prediction) return

      try {
        const formData = new FormData()
        const response = await axios.get(frame.url, { responseType: 'blob' })
        formData.append('image', response.data, 'frame.jpg')
        const predictionResponse = await axios.post(`${process.env.VUE_APP_PREDICTION_API_URL}/predict`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        frame.prediction = predictionResponse.data
      } catch (error) {
        console.error(error)
      }
    }

    const getRiskClass = (prediction) => {
      if (!prediction) return ''
      const probability = prediction.probability
      if (probability >= 0.9) return 'very-high-risk'
      if (probability >= 0.7) return 'high-risk'
      if (probability >= 0.5) return 'risky'
      return 'no-fire'
    }

    const getRiskLevel = (prediction) => {
      if (!prediction) return ''
      const probability = prediction.probability
      if (probability >= 0.9) return 'Çok Yüksek Risk'
      if (probability >= 0.7) return 'Yüksek Risk'
      if (probability >= 0.5) return 'Riskli'
      return 'Yangın Yok'
    }

    const formatProbability = (probability) => {
      return (probability * 100).toFixed(2) + '%'
    }

    const formatTimestamp = (timestamp) => {
      const date = new Date(`${timestamp.slice(0, 4)}-${timestamp.slice(4, 6)}-${timestamp.slice(6, 8)}T${timestamp.slice(9, 11)}:${timestamp.slice(11, 13)}:${timestamp.slice(13, 15)}`)
      return date.toLocaleString()
    }

    const filteredFrames = computed(() => {
      return frames.value.filter(frame => frame.prediction && frame.prediction.probability >= 0.5)
    })

    onMounted(() => {
      checkFrames()
    })

    return {
      frames,
      filteredFrames,
      getRiskClass,
      getRiskLevel,
      formatProbability,
      formatTimestamp,
      rtspIp
    }
  }
}
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

.container {
  max-width: 800px;
  margin: 0 auto;
}

.card {
  transition: all 0.3s ease-in-out;
}

.card:hover {
  transform: scale(1.05);
}
</style>
