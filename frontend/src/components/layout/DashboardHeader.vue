<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { fetchHealth } from '@/services/api'

const store = useDemoStore()
const backendOnline = ref(false)
const backendMockMode = ref<boolean | null>(null)
const modeInitialized = ref(false)
let healthTimer: any = null

async function checkHealth() {
  try {
    const h: any = await fetchHealth()
    backendOnline.value = true
    backendMockMode.value = Boolean(h.mockMode)
    // 仅首次根据后端默认模式初始化，之后尊重用户手动切换
    if (!modeInitialized.value) {
      store.mockMode = Boolean(h.mockMode)
      modeInitialized.value = true
    }
  } catch {
    backendOnline.value = false
  }
}

onMounted(() => {
  checkHealth()
  healthTimer = setInterval(checkHealth, 5000)
})

onUnmounted(() => clearInterval(healthTimer))
</script>

<template>
  <header class="h-14 bg-white flex items-center justify-between px-6 border-b border-slate-200/80">
    <div class="flex items-center gap-3 min-w-0">
      <div class="w-8.5 h-8.5 rounded-lg bg-gradient-to-br from-sky-500 to-blue-700 flex items-center justify-center shadow-sm flex-shrink-0">
        <svg class="w-4.5 h-4.5 text-white" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>
      <div class="min-w-0">
        <div class="text-[16px] font-bold text-slate-900 tracking-tight truncate">VGuard 大模型推理验证器的水印注入与版权保护平台</div>
      </div>
    </div>

    <div class="flex items-center gap-3 flex-shrink-0">
      <span class="status-pill status-pill-ok">
        <span class="status-dot bg-emerald-500" />
        {{ backendOnline ? 'API 在线' : 'API 离线' }}
      </span>
      <span v-if="backendOnline && backendMockMode !== null" class="status-pill status-pill-info">
        后端默认：{{ backendMockMode ? '沙箱评测' : '真实模型' }}
      </span>

      <label class="flex items-center gap-2 cursor-pointer select-none">
        <span class="text-[10px] font-medium text-slate-500">前端运行模式（可手动切换）</span>
        <button
          type="button"
          class="relative inline-flex h-4.5 w-8 items-center rounded-full transition-colors"
          :class="store.mockMode ? 'bg-sky-600' : 'bg-slate-200'"
          @click="store.mockMode = !store.mockMode"
        >
          <span class="block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform" :class="store.mockMode ? 'translate-x-4' : 'translate-x-0.5'" />
        </button>
      </label>
    </div>
  </header>
</template>
