import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

// Pinia 管理跨组件共享的客户端状态。
app.use(createPinia())

// Vue Router 负责页面路由和布局切换。
app.use(router)

app.mount('#app')
