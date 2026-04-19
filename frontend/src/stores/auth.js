import { ref, computed } from "vue"
import api from "../services/api"

const TOKEN_KEY = 'irrigation_token'
const USER_KEY = 'irrigation_user'

const token = ref(localStorage.getItem(TOKEN_KEY))
const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

const isAuthenticated = computed(() => !!token.value)

async function register({ name, email, password }) {
    const { data } = await api.post('/auth/register', { name, email, password })
    return data
}

async function login({ email, password }) {
    const { data } = await api.post('/auth/login', { email, password })
    token.value = data.access_token
    localStorage.setItem(TOKEN_KEY, token.value)
    user.value = { email }
    localStorage.setItem(USER_KEY, JSON.stringify(user.value))
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
        register,
        login,
        logout,
    }
}