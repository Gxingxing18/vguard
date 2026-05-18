<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNavigationStore } from '@/stores/navigation'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'

const auth = useAuthStore()
const nav = useNavigationStore()
const ready = computed(() => auth.ready)

onMounted(async () => {
  await auth.bootstrap()
  nav.push(auth.isAuthenticated ? 'home' : 'login')
})

watch(
  () => auth.isAuthenticated,
  (value) => {
    nav.push(value ? 'home' : 'login')
  },
)
</script>

<template>
  <LoginView v-if="ready && nav.route === 'login'" />
  <DashboardView v-else-if="ready && nav.route === 'home'" />
  <div v-else class="min-h-screen bg-white" />
</template>
