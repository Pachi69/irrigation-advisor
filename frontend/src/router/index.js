import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import FieldList from '../views/FieldList.vue'
import FieldRegister from '../views/FieldRegister.vue'
import FieldDetail from '../views/FieldDetail.vue'
import FieldEdit from '../views/FieldEdit.vue'
import SectorRegister from '../views/SectorRegister.vue'
import SectorRecommendation from '../views/SectorRecommendation.vue'
import SectorHistory from '../views/SectorHistory.vue'
import SectorChart from '../views/SectorChart.vue'
import SectorConfirmations from '../views/SectorConfirmations.vue'
import SectorEdit from '../views/SectorEdit.vue'
import AdminFields from '../views/AdminFields.vue'
import Account from '../views/Account.vue'
import { useAuth } from '../stores/auth'
import SectorMetrics from '../views/SectorMetrics.vue'
import DemoView from '../views/DemoView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { requiresAuth: true },
  },
  {
    path: '/account',
    name: 'account',
    component: Account,
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
    path: '/fields/:id',
    name: 'field-detail',
    component: FieldDetail,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/:id/edit',
    name: 'field-edit',
    component: FieldEdit,
    meta: { requiresAuth: true },
  },
  {
    path: '/fields/:id/sectors/new',
    name: 'sector-register',
    component: SectorRegister,
    meta: { requiresAuth: true },
  },
  {
    path: '/sectors/:id/recommendation',
    name: 'sector-recommendation',
    component: SectorRecommendation,
    meta: { requiresAuth: true },
  },
  {
    path: '/sectors/:id/history',
    name: 'sector-history',
    component: SectorHistory,
    meta: { requiresAuth: true },
  },
  {
    path: '/sectors/:id/chart',
    name: 'sector-chart',
    component: SectorChart,
    meta: { requiresAuth: true },
  },
  {
    path: '/sectors/:id/confirmations',
    name: 'sector-confirmations',
    component: SectorConfirmations,
    meta: { requiresAuth: true },
  },
  {
    path: '/sectors/:id/edit',
    name: 'sector-edit',
    component: SectorEdit,
    meta: { requiresAuth: true },
  },
  {
      path: '/sectors/:id/metrics',
      name: 'sector-metrics',
      component: SectorMetrics,
      meta: { requiresAuth: true },
  },
  {
    path: '/admin/fields',
    name: 'admin-fields',
    component: AdminFields,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/demo',
    name: 'demo',
    component: DemoView,
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