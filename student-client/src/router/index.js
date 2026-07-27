import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import StudentHome from '../views/StudentHome.vue'
import { API_BASE } from '../config.js'

const routes = [
  { path: '/login', component: Login },
  { path: '/', component: StudentHome },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  if (to.path === '/login') return

  const token = localStorage.getItem('kp_student_token')
  if (!token) return '/login'

  // 加超时，防止卡死
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 3000)

  try {
    const r = await fetch(API_BASE + '/api/auth/me', {
      headers: { 'Authorization': 'Bearer ' + token },
      signal: controller.signal
    })
    clearTimeout(timer)
    if (r.ok) return
  } catch { clearTimeout(timer) }

  return '/login'
})

export default router
