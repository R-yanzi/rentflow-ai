/// <reference types="vite/client" />

/**
 * Vite 只会把以 VITE_ 开头的环境变量暴露给浏览器代码。
 * 不要在这里放数据库密码、API Key 等服务端密钥。
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
