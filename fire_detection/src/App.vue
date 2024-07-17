<template>
  <div id="app" class="container">
    <h1>Fire Detection App</h1>
    <div class="upload-section">
      <input type="file" @change="onFileChange" />
      <button @click="uploadImage">Upload</button>
    </div>
    <div v-if="imageUrl" class="image-preview">
      <h2>Uploaded Image:</h2>
      <img :src="imageUrl" alt="Uploaded Image" />
    </div>
    <div v-if="result" class="result-section" :class="{'fire-detected': result.predicted_class === 'fire', 'no-fire': result.predicted_class === 'no fire'}">
      <h2>Result:</h2>
      <p>Predicted Class: {{ result.predicted_class }}</p>
      <p>Probability: {{ result.probability }}</p>
    </div>
    <div v-if="error" class="error-section">
      <p>Error: {{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      imageFile: null,
      imageUrl: null,
      result: null,
      error: null,
    };
  },
  methods: {
    onFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.imageFile = file;
        this.imageUrl = URL.createObjectURL(file);
      }
    },
    async uploadImage() {
      if (!this.imageFile) {
        alert("Please select an image file first.");
        return;
      }

      const formData = new FormData();
      formData.append('image', this.imageFile);

      try {
        const response = await axios.post('http://127.0.0.1:5000/predict', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        this.result = response.data;
        this.error = null;
      } catch (error) {
        this.error = error.response ? error.response.data : error.message;
        this.result = null;
      }
    },
  },
};
</script>

<style>
.container {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  font-family: Arial, sans-serif;
}

.upload-section {
  margin-bottom: 20px;
}

.image-preview {
  margin-top: 20px;
}

.image-preview img {
  max-width: 100%;
  height: auto;
}

.result-section {
  margin-top: 20px;
  padding: 20px;
  border-radius: 8px;
}

.result-section.fire-detected {
  background-color: #ffcccc;
  color: #cc0000;
}

.result-section.no-fire {
  background-color: #ccffcc;
  color: #006600;
}

.error-section {
  margin-top: 20px;
  color: #cc0000;
}
</style>
