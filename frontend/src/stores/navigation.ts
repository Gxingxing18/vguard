import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useNavigationStore = defineStore('navigation', () => {
  const route = ref<'login' | 'home'>('login')

  const isLoginRoute = computed(() => route.value === 'login')

  function push(target: 'login' | 'home') {
    route.value = target
  }

  return {
    route,
    isLoginRoute,
    push,
  }
})
