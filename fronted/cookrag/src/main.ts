import { createRouter, createWebHistory } from 'vue-router'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import Chat from '@/views/Chat.vue'
import Recipe from '@/views/Recipe.vue'
import History from '@/views/History.vue'

const router = createRouter({
    history: createWebHistory(),
    routes:[
        {
            path: "/",
            name:"Chat",
            component: Chat
        },
        {
            path: "/recipe",
            name:"Recipe",
            component: Recipe
        },
        {
            path: "/history",
            name:"History",
            component: History
        }
    ]
})


const app = createApp(App)
const pinia = createPinia

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(pinia)

app.mount('#app')
