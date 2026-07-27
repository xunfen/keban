<template>
  <div class="net-badge" :class="status">
    <span class="net-dot"></span> {{ text }}
  </div>
</template>

<script setup>
import { ref,onMounted,onUnmounted } from 'vue'
const status=ref('online'); const text=ref('已联网')
function u(){status.value=navigator.onLine?'online':'offline';text.value=status.value==='online'?'已联网':'离线模式'}
onMounted(()=>{u();window.addEventListener('online',u);window.addEventListener('offline',u)})
onUnmounted(()=>{window.removeEventListener('online',u);window.removeEventListener('offline',u)})
</script>
