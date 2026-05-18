<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { fetchHealth } from '@/services/api'

const store = useDemoStore()
const backendOnline = ref(false)
let healthTimer: any = null

async function checkHealth() {
  try {
    const h: any = await fetchHealth()
    backendOnline.value = true
    if (!h.mockMode) store.mockMode = false
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
        <div class="flex items-baseline gap-2">
          <span class="text-[16px] font-bold text-slate-900 tracking-tight">VGuard</span>
          <span class="text-[11px] text-slate-500 truncate">大模型验证器水印评测平台</span>
        </div>
        <div class="text-[10px] text-slate-400 truncate">行为偏移验证与版权归属判定</div>
      </div>
    </div>

    <div class="flex items-center gap-3 flex-shrink-0">
      <span class="status-pill status-pill-ok">
        <span class="status-dot bg-emerald-500" />
        {{ backendOnline ? 'API 在线' : 'API 离线' }}
      </span>

      <label class="flex items-center gap-2 cursor-pointer select-none">
        <span class="text-[10px] font-medium text-slate-500">沙箱评测</span>
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
