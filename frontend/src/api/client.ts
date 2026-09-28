/** 统一请求封装：拼后端地址、带上当前值班账号、抛网络错误、给页脚留一句可读的说明。 */
import { getActivePinia } from 'pinia'

import { useSessionStore } from '@/stores/session'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''

function buildHeaders(init?: RequestInit): HeadersInit {
  const headers = new Headers(init?.headers)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  // 通行区域权限按值班账号过滤；在 pinia 尚未激活（如单测）时回落为默认管理员
  if (getActivePinia()) {
    const session = useSessionStore()
    headers.set('X-Operator-Id', session.operatorId)
  }
  return headers
}

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  return fetch(url, {
    ...init,
    headers: buildHeaders(init),
  }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new Error(`接口请求失败：${detail}`)
  })
}

/** 优先读取后端返回的可读 detail/message，兜底用传入的默认提示。 */
export async function responseError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string; message?: string }
    return payload.detail || payload.message || fallback
  } catch {
    return fallback
  }
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await request(path)
  if (!response.ok) {
    throw new Error(await responseError(response, `接口返回 ${response.status}，数据未更新`))
  }
  return (await response.json()) as T
}
