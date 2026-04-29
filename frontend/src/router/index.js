import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import FieldList from '../views/FieldList.vue'
import FieldRegister from '../views/FieldRegister.vue'
import { useAuth } from '../stores/auth'
import AdminFields from '../views/AdminFields.vue'
import FieldRecommendation from '../views/FieldRecommendation.vue'
import FieldHistory from '../views/FieldHistory.vue'
import FieldEdit from '../views/FieldEdit.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields',
    name: 'fields',
    component: FieldList,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/new',
    name: 'field-register',
    component: FieldRegister,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/:id/edit',
    name: 'field-edit',
    component: FieldEdit,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/:id/recommendation',
    name: 'field-recommendation',
    component: FieldRecommendation,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/:id/history',
    name: 'field-history',
    component: FieldHistory,
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/fields',
    name: 'admin-fields',
    component: AdminFields,
    meta: { requiresAuth: true, requiresAdmin: true },
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
    const { isAuthenticated, isAdmin } = useAuth()

    if (to.meta.requiresAuth && !isAuthenticated.value) {
        return { name: 'login' }
    }

    if (to.meta.guestOnly && isAuthenticated.value) {
        return { name: 'home' }
    }

    if (to.meta.requiresAdmin && !isAdmin.value) {
        return { name: 'home' }
    }
})

export default router