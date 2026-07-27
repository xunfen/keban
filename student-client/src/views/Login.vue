<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-emoji">🧑‍🎓</div>
      <h1>课伴 · 学生端</h1>
      <p class="login-sub">输入老师给你的账号密码登录</p>
      <div v-if="error" class="login-error-box">{{ error }}</div>
      <div class="login-body">
        <input v-model="username" type="text" placeholder="用户名" style="margin-bottom:10px" @keyup.enter="doLogin" />
        <input v-model="password" type="password" placeholder="密码" @keyup.enter="doLogin" />
        <button type="button" class="btn btn-primary login-btn" :disabled="!username.trim()||!password||logging" @click="doLogin">
          {{ logging ? '登录中…' : '进入学习 🚀' }}
        </button>
        <p class="login-hint">没有账号？请联系老师创建</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../config.js'

const router = useRouter()
const username = ref(''); const password = ref(''); const error = ref(''); const logging = ref(false)

async function doLogin() {
  error.value = ''
  if (!username.value.trim() || !password.value) return
  logging.value = true
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 8000)
  try {
    const r = await fetch(API_BASE + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value.trim(), password: password.value }),
      signal: controller.signal
    })
    clearTimeout(timer)
    const d = await r.json()
    if (d.token && d.role === 'student') {
      localStorage.setItem('kp_student_token', d.token)
      localStorage.setItem('kp_student_name', d.display_name || d.username)
      router.push('/')
      return
    }
    error.value = d.error || '登录失败，请检查账号密码'
  } catch (e) {
    clearTimeout(timer)
    if (e.name === 'AbortError') {
      error.value = '请求超时（8秒），请确认后端正在运行在 localhost:5000'
    } else {
      error.value = '无法连接服务器：' + e.message
    }
  }
  logging.value = false
}
</script>

<style scoped>
.login-wrapper{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#fef3c7,#fce7f3)}
.login-card{background:#fff;border-radius:24px;padding:48px 40px;width:400px;max-width:92vw;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.08)}
.login-emoji{font-size:64px;margin-bottom:8px}
.login-card h1{font-size:26px;color:#1c1917}
.login-sub{color:#78716c;font-size:14px;margin:8px 0 24px}
.login-error-box{background:#fee2e2;color:#dc2626;padding:10px;border-radius:10px;font-size:13px;margin-bottom:12px}
.login-body{text-align:left}
.login-card input{margin-bottom:8px;background:#fffbeb}
.login-btn{width:100%;justify-content:center;margin-top:4px;background:linear-gradient(135deg,#f59e0b,#f97316);color:#fff}
.login-hint{text-align:center;font-size:12px;color:#a8a29e;margin-top:16px}
</style>
