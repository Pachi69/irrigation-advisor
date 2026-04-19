<script setup>
import {ref, onMounted} from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { useAuth } from '../stores/auth'


const router = useRouter()
const { user, logout } = useAuth()

const status = ref(null)
const error = ref(null)

onMounted(async () => {
    try {
        const response = await api.get('/health')
        status.value = response.data 
    } catch (err) {
        error.value = err.message
    }
})

function handleLogout() {
    logout()
    router.push('/login')
}

</script>

<template>
    <h1>Irrigation Advisor</h1>
    <p v-if="user">Bienvenido, <strong>{{ user.email }}</strong>.</p>

    <section>
        <h2>Estado del backend</h2>
        <p v-if="status">
            Conectado — estado: <strong>{{ status.status }}</strong>,
            entorno: <strong>{{ status.environment }}</strong>
        </p>
        <p v-else-if="error" style="color: red">Error al conectar: {{ error }}</p>
        <p v-else>Conectando al backend...</p>
    </section>

    <button @click="handleLogout">Cerrar sesión</button>
</template>

<style scoped>
button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}
</style>