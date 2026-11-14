import { httpClient } from './http'

/**
 * 对应 FastAPI 的 HealthResponse。
 *
 * status 使用字面量类型，可以防止前端误把任意字符串
 * 当作服务正常状态。
 */
export interface HealthResponse {
  status: 'ok'
  service: string
  version: string
}

/**
 * 检查 FastAPI 进程是否正常响应。
 */
export async function getHealth(): Promise<HealthResponse> {
  const response = await httpClient.get<HealthResponse>('/health')
  return response.data
}
