import { ref, computed } from "vue"
import api from "../services/api"

const TOKEN_KEY = 'irrigation_token'
const USER_KEY = 'irrigation_user'

const token = ref(localStorage.getItem(TOKEN_KEY))
const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

const isAuthenticated = computed(() => !!token.value)
const isAdmin = computed(() => user.value?.role === 'admin') 

async function fetchMe() {
    // Trae al usuario atenticado desde el backend usando el token actual
    const { data } = await api.get('/auth/me')
    user.value = data
    localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    return data
}

async function register({ name, email, password }) {
    const { data } = await api.post('/auth/register', { name, email, password })
    return data
}

async function login({ email, password }) {
    const { data } = await api.post('/auth/login', { email, password })
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, token.value)
    // Cargamos el perfil completo (incluye role) para poder renderizar UI condicional
    await fetchMe()
    return data
}

function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
}

export function useAuth() {
    return {
        token,
        user,
        isAuthenticated,
        isAdmin,
        register,
        login,
        logout,
        fetchMe,
    }
}