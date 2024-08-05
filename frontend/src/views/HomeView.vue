<template>
  <div class="container mt-5">
    <h1 class="text-center mb-4">Log</h1>
    <div class="terminal">
      <pre class="logInside">{{ logs.join('\n') }}</pre>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'

export default {
  setup() {
    const logs = ref([])

    const addLog = (message) => {
      logs.value.unshift(`[${new Date().toLocaleTimeString()}] ${message}`)
      if (logs.value.length > 100) {
        logs.value.pop()
      }
    }

    onMounted(() => {
      // Log ekleme fonksiyonu
      addLog('Log sayfası yüklendi')
    })

    onBeforeUnmount(() => {
      // Sayfa kapatılırken yapılacak işlemler
    })

    return {
      logs
    }
  }
}
</script>

<style>
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

.logInside {
  color: rgb(142, 143, 143);
}
</style>
