<template>
  <div class="setup-wrapper">
    <div class="setup-card">
      <div class="setup-emoji">{{ step===1?'🔑':'👨‍🏫' }}</div>
      <h1>课伴 · 首次配置</h1>
      <p class="setup-sub">{{ step===1?'请配置API Key，再创建教师账号':'创建教师账号，用于登录管理' }}</p>

      <!-- Step 1: API Key -->
      <div v-if="step===1" class="setup-body">
        <p class="setup-label">🔑 DashScope API Key</p>
        <input v-model="apiKey" type="text" placeholder="sk-..." />
        <p class="setup-hint">获取地址：<a href="https://dashscope.aliyun.com/" target="_blank">dashscope.aliyun.com</a> ｜ 新用户免费</p>
        <button class="btn btn-primary setup-btn" :disabled="!apiKey.trim()||saving" @click="saveKey">
          {{ saving ? '保存中…' : '下一步' }}
        </button>
      </div>

      <!-- Step 2: Teacher account -->
      <div v-if="step===2" class="setup-body">
        <p class="setup-label">👤 教师账号</p>
        <input v-model="teacherUser" type="text" placeholder="用户名（如：zhangsan）" style="margin-bottom:10px" />
        <input v-model="teacherPass" type="password" placeholder="密码（至少6位）" style="margin-bottom:10px" />
        <input v-model="teacherName" type="text" placeholder="显示名称（如：张老师）" />
        <button class="btn btn-primary setup-btn" :disabled="!teacherUser.trim()||teacherPass.length<6||saving2" @click="createTeacher" style="margin-top:12px">
          {{ saving2 ? '创建中…' : '创建账号并开始使用 🚀' }}
        </button>
        <p v-if="error" class="setup-error">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../config.js'

const router = useRouter()
const step = ref(1)
const apiKey = ref(''); const saving = ref(false)
const teacherUser = ref(''); const teacherPass = ref(''); const teacherName = ref('')
const saving2 = ref(false); const error = ref('')

onMounted(async () => {
  try {
    const r = await fetch(API_BASE+'/api/health')
    const d = await r.json()
    if (d.configured && d.has_teacher) router.push('/login')
  } catch {}
})

async function saveKey() {
  error.value=''
  if (!apiKey.value.trim().startsWith('sk-')) { error.value='Key 应以 sk- 开头'; return }
  step.value = 2
}

async function createTeacher() {
  error.value=''; saving2.value=true
  try {
    const r=await fetch(API_BASE+'/api/setup/init',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      api_key: apiKey.value.trim(),
      username: teacherUser.value.trim(),
      password: teacherPass.value,
      display_name: teacherName.value.trim() || teacherUser.value.trim()
    })})
    const d=await r.json()
    if(d.ok) router.push('/login')
    else error.value=d.error||'创建失败'
  } catch(e) { error.value='无法连接服务器：'+e.message }
  saving2.value=false
}
</script>

<style scoped>
.setup-wrapper{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#eff6ff,#fef3c7)}
.setup-card{background:#fff;border-radius:24px;padding:48px 40px;width:420px;max-width:92vw;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.08)}
.setup-emoji{font-size:64px;margin-bottom:8px}
.setup-card h1{font-size:26px;color:#1e293b}
.setup-sub{color:#64748b;font-size:14px;margin:8px 0 24px}
.setup-body{text-align:left}
.setup-label{font-size:14px;font-weight:600;color:#475569;margin-bottom:6px}
.setup-card input{margin-bottom:4px}
.setup-hint{font-size:12px;color:#94a3b8;margin-bottom:16px}
.setup-hint a{color:#2563eb}
.setup-btn{width:100%;justify-content:center}
.setup-error{color:#dc2626;font-size:13px;margin-top:8px}
</style>
