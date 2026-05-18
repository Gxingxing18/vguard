import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { login as apiLogin, fetchMe, logout as apiLogout } from '@/services/auth'

const TOKEN_KEY = 'vguard_auth_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const username = ref('')
  const ready = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value))

  function setToken(value: string) {
    token.value = value
    if (value) localStorage.setItem(TOKEN_KEY, value)
    else localStorage.removeItem(TOKEN_KEY)
  }

  async function bootstrap() {
    if (!token.value) {
      ready.value = true
      return
    }
    try {
      const me = await fetchMe(token.value)
      username.value = me.username
    } catch {
      setToken('')
      username.value = ''
    } finally {
      ready.value = true
    }
  }

  async function login(usernameInput: string, password: string) {
    const res = await apiLogin(usernameInput, password)
    username.value = res.username
    setToken(res.token)
  }

  async function logout() {
    if (token.value) {
      try {
        await apiLogout(token.value)
      } catch {
        // ignore
      }
    }
    setToken('')
    username.value = ''
  }

  return {
    token,
    username,
    ready,
    isAuthenticated,
    bootstrap,
    login,
    logout,
  }
})
