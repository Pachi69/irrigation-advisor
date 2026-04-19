<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <nav>
    <RouterLink to="/">Home</RouterLink> |
    <RouterLink to="/login">Login</RouterLink> |
    <RouterLink to="/register">Registro</RouterLink>
  </nav>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
nav {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
}
main {
  padding: 1rem;
}
</style>