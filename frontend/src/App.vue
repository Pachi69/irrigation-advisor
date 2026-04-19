<script setup>
import { RouterView, RouterLink, useRouter } from 'vue-router'
import { useAuth } from './stores/auth'

const router = useRouter()
const { isAuthenticated, logout } = useAuth()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <nav>
    <template v-if="isAuthenticated">
      <RouterLink to="/">Home</RouterLink>
      <button class="link-btn" @click="handleLogout">Cerrar sesión</button>
    </template>
    <template v-else>
      <RouterLink to="/login">Login</RouterLink>
      <span class="separator">|</span>
      <RouterLink to="/register">Registro</RouterLink>
    </template>
  </nav>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
nav {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.separator {
  color: #999;
}
.link-btn {
  background: none;
  border: none;
  color: #1976d2;
  cursor: pointer;
  font-size: 1rem;
  padding: 0;
  text-decoration: underline;
}
main {
  padding: 1rem;
}
</style>