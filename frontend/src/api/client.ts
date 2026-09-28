/** 统一请求封装：拼后端地址、携带账号区域权限、抛网络错误、给页脚留一句可读的说明。 */
import { useSessionStore } from '@/stores/session'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const session = useSessionStore()
  const headers = new Headers({ 'Content-Type': 'application/json' })
  if (init?.headers) {
    new Headers(init.headers).forEach((value, key) => headers.set(key, value))
  }
  headers.set('X-Account-Name', session.operator)
  if (Array.isArray(session.managedAreas)) {
    headers.set('X-Managed-Areas', session.managedAreas.join(','))
  }

  return fetch(url, { ...init, headers }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new Error(`接口请求失败：${detail}`)
  })
}

export async function readErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown; message?: unknown }
    if (typeof payload.detail === 'string' && payload.detail) {
      return payload.detail
    }
    if (typeof payload.message === 'string' && payload.message) {
      return payload.message
    }
  } catch {
    // JSON 解析失败时使用调用方给出的兜底说明。
  }
  return fallback
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await request(path)
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, `接口返回 ${response.status}，数据未更新`))
  }
  return (await response.json()) as T
}
