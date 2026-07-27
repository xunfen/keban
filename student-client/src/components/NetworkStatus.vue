<template>
  <span class="flex" style="gap:4px">
    <span class="net-dot" :style="{background:color}"></span>{{ text }}
  </span>
</template>
<script setup>
import { ref,computed,onMounted,onUnmounted } from 'vue'
const online=ref(true)
const text=computed(()=>online.value?'在线':'离线')
const color=computed(()=>online.value?'#10b981':'#ef4444')
function u(){online.value=navigator.onLine}
onMounted(()=>{u();window.addEventListener('online',u);window.addEventListener('offline',u)})
onUnmounted(()=>{window.removeEventListener('online',u);window.removeEventListener('offline',u)})
</script>
