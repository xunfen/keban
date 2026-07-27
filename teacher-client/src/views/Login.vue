<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-emoji">📖</div>
      <h1>课伴 · 教师端</h1>
      <p class="login-sub">欢迎回来，请登录</p>
      <div class="login-body">
        <input v-model="username" type="text" placeholder="教师账号" style="margin-bottom:10px" @keyup.enter="doLogin" />
        <input v-model="password" type="password" placeholder="密码" @keyup.enter="doLogin" />
        <p v-if="error" class="login-error">{{ error }}</p>
        <button class="btn btn-primary login-btn" :disabled="!username.trim()||!password||logging" @click="doLogin">
          {{ logging ? '登录中…' : '登录 👨‍🏫' }}
        </button>
        <p class="login-hint">首次使用？请联系管理员配置</p>
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
  error.value=''; logging.value=true
  try {
    const r=await fetch(API_BASE+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:username.value.trim(),password:password.value})})
    const d=await r.json()
    if(d.token) {
      localStorage.setItem('kp_teacher_token', d.token)
      localStorage.setItem('kp_teacher_name', d.display_name||d.username)
      router.push('/')
    } else { error.value=d.error||'登录失败' }
  } catch(e) { error.value='无法连接服务器：'+e.message }
  logging.value=false
}
</script>

<style scoped>
.login-wrapper{min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#eff6ff,#fef3c7)}
.login-card{background:#fff;border-radius:24px;padding:48px 40px;width:400px;max-width:92vw;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.08)}
.login-emoji{font-size:64px;margin-bottom:8px}
.login-card h1{font-size:26px;color:#1e293b}
.login-sub{color:#64748b;font-size:14px;margin:8px 0 24px}
.login-body{text-align:left}
.login-card input{margin-bottom:8px}
.login-btn{width:100%;justify-content:center;margin-top:4px}
.login-error{color:#dc2626;font-size:13px;margin:8px 0}
.login-hint{text-align:center;font-size:12px;color:#94a3b8;margin-top:16px}
</style>
