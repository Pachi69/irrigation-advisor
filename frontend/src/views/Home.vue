<script setup>
import {ref, onMounted} from 'vue'
import api from '../services/api'

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
</script>

<template>
    <h1> Irrigation Advisor</h1>
    <p> Bienvenido al sistema de recomendacion de riego.</p>

    <section>
        <h2> Estado del bacekdn</h2>
        <p v-if="status">
            Conectado - estado: <strong>{{ status.status }}</strong>, entorno: <strong>{{ status.environment }}</strong>
        </p>
        <p v-else-if="error" style="color: red"> Error al conectar: {{ error }}</p>
        <p v-else> Conectando al backend...</p>
    </section>
</template>