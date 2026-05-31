import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type RouteName = 'landing' | 'login' | 'home'

export const useNavigationStore = defineStore('navigation', () => {
  const route = ref<RouteName>('landing')

  const isLoginRoute = computed(() => route.value === 'login')

  function push(target: RouteName) {
    route.value = target
  }

  return {
    route,
    isLoginRoute,
    push,
  }
})
