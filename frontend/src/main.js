import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Lazyload } from 'vant'
import App from './App.vue'
import router from './router'
import './styles/index.css'
// Vant 全量样式（含 Toast/Dialog 等函数式组件的样式）
import 'vant/lib/index.css'

const app = createApp(App)
app.use(createPinia())
app.use(Lazyload) // van-image lazy-load 图片懒加载
app.use(router)
app.mount('#app')
