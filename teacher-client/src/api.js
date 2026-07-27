/**
 * API 请求封装
 * 开发环境用 Vite 代理，部署时自动拼接服务器地址
 */
import { API_BASE } from '../config.js'

async function request(path, options = {}) {
  const url = API_BASE + path
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })
  return res.json()
}

export function get(path) {
  return fetch(API_BASE + path).then(r => r.json())
}

export function post(path, data) {
  return request(path, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function upload(path, formData) {
  return fetch(API_BASE + path, {
    method: 'POST',
    body: formData,
  }).then(r => r.json())
}

export { API_BASE }
