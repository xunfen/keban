import { createRouter, createWebHistory } from 'vue-router'
import Setup from '../views/Setup.vue'
import Login from '../views/Login.vue'
import TeacherDashboard from '../views/TeacherDashboard.vue'
import { API_BASE } from '../config.js'

const routes = [
  { path: '/setup', component: Setup },
  { path: '/login', component: Login },
  { path: '/', component: TeacherDashboard },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  if (to.path === '/setup') return

  if (to.path === '/login') {
    try {
      const c = new AbortController()
      setTimeout(() => c.abort(), 3000)
      const r = await fetch(API_BASE + '/api/health', { signal: c.signal })
      const d = await r.json()
      if (!d.configured) return '/setup'
    } catch {}
    return
  }

  // 检查初始化
  try {
    const c = new AbortController()
    setTimeout(() => c.abort(), 3000)
    const r = await fetch(API_BASE + '/api/health', { signal: c.signal })
    const d = await r.json()
    if (!d.configured) return '/setup'
    if (!d.has_teacher) return '/setup'
  } catch { return '/setup' }

  const token = localStorage.getItem('kp_teacher_token')
  if (!token) return '/login'

  try {
    const c = new AbortController()
    setTimeout(() => c.abort(), 3000)
    const r = await fetch(API_BASE + '/api/auth/me', {
      headers: { 'Authorization': 'Bearer ' + token },
      signal: c.signal
    })
    if (r.ok) return
  } catch {}

  return '/login'
})

export default router
