import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setupElementPlus } from './plugins/element-plus'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 配置Element Plus
setupElementPlus(app)

app.mount('#app')
