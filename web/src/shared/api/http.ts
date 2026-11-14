import axios from 'axios'

/**
 * RentFlow AI 统一 HTTP 客户端。
 *
 * 所有后端请求都通过这个实例发送，便于后续统一配置：
 * - API 基础地址
 * - 请求超时
 * - 身份认证 Token
 * - 错误处理
 * - 请求日志
 */
export const httpClient = axios.create({
  // 开发环境默认请求 /api/v1。
  // Vite 后续会将 /api 请求代理到本地 FastAPI。
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',

  // 避免后端异常时请求无限等待。
  timeout: 10_000,

  headers: {
    'Content-Type': 'application/json',
  },
})
