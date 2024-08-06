<template>
  <div class="container mt-5">
    <h1 class="text-center mb-4">Yakalanan Yangın Kareleri</h1>
    <div v-if="frames.length" class="frames-section">
      <div class="row">
        <div v-for="(frame, index) in frames" :key="index" class="col-12 mb-4">
          <div class="card shadow-sm p-3 mb-5 bg-white rounded">
            <img :src="'data:image/jpeg;base64,' + frame.data" class="card-img-top" :alt="'Kare ' + (index + 1)" />
            <div class="card-body">
              <h5 class="card-title">Dosya Adı: {{ frame.filename }}</h5>
              <p class="card-text">Yüklenme Zamanı: {{ formatTimestamp(frame.uploadDate) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="text-center">
      <p>Henüz yakalanan yangın karesi yok.</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { ref, onMounted } from 'vue'

export default {
  setup() {
    const frames = ref([])

    const fetchFrames = async () => {
      try {
        const response = await axios.get(`${process.env.VUE_APP_BACKEND_URL}/api/photos`)
        if (response.status === 200) {
          frames.value = response.data.map((photo) => ({
            ...photo,
            uploadDate: new Date(photo.uploadDate).toLocaleString()
          }))
        }
      } catch (error) {
        console.error(error)
      }
    }

    const formatTimestamp = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    onMounted(() => {
      fetchFrames()
    })

    return {
      frames,
      formatTimestamp
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
