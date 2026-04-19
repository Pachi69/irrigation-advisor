import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import { useAuth } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: { guestOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
    const { isAuthenticated } = useAuth()

    if (to.meta.requiresAuth && !isAuthenticated.value) {
        return { name: 'login' }
    }

    if (to.meta.guestOnly && isAuthenticated.value) {
        return { name: 'home' }
    }
})

export default router