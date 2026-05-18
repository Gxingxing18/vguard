<script setup lang="ts">
import { computed } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { useAuthStore } from '@/stores/auth'
import DashboardHeader from '@/components/layout/DashboardHeader.vue'
import PanelInjection from '@/components/panels/PanelInjection.vue'
import PanelReasoningEffect from '@/components/panels/PanelReasoningEffect.vue'
import PanelVerification from '@/components/panels/PanelVerification.vue'
import PanelStatistics from '@/components/panels/PanelStatistics.vue'

const store = useDemoStore()
const auth = useAuthStore()

const panels: Record<string, any> = {
  injection: PanelInjection,
  reasoning: PanelReasoningEffect,
  verification: PanelVerification,
  statistics: PanelStatistics,
}

const currentPanel = computed(() => panels[store.activeTab] || PanelInjection)

const tabs = [
  { value: 'injection' as const, label: '水印注入', desc: '训练与注入' },
  { value: 'reasoning' as const, label: '推理偏移对比', desc: '排序差异' },
  { value: 'verification' as const, label: '版权归属验证', desc: '统计检验' },
  { value: 'statistics' as const, label: '统计证据', desc: '图表分析' },
]
</script>

<template>
  <div class="h-screen bg-white flex flex-col overflow-hidden">
    <DashboardHeader />

    <div class="flex flex-1 min-h-0">
      <aside class="w-56 bg-white border-r border-slate-200/70 flex-shrink-0 flex flex-col py-5 px-3.5">
        <nav class="space-y-1.5">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="group relative w-full flex flex-col px-3.5 py-3 rounded-lg text-left transition-all duration-200"
            :class="store.activeTab === tab.value ? 'bg-sky-50 border border-sky-100' : 'border border-transparent hover:bg-slate-50'"
            @click="store.activeTab = tab.value"
          >
            <span class="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-sky-600 transition-all duration-300" :class="store.activeTab === tab.value ? 'opacity-100 scale-y-100' : 'opacity-0 scale-y-50'" />
            <span class="text-[13px] font-semibold leading-tight" :class="store.activeTab === tab.value ? 'text-slate-900' : 'text-slate-600 group-hover:text-slate-800'">{{ tab.label }}</span>
            <span class="text-[11px] text-slate-400 mt-0.5">{{ tab.desc }}</span>
          </button>
        </nav>

        <div class="mt-auto pt-5">
          <div class="px-3.5 py-3 rounded-lg bg-sky-50 border border-sky-100">
            <div class="text-[10px] font-semibold tracking-wide text-sky-700 mb-1.5">项目概览</div>
            <div class="text-[11px] text-slate-600 leading-4 line-clamp-2">
              面向大模型推理验证器的水印注入、行为偏移验证与版权归属判定平台。
            </div>
            <button class="mt-2.5 text-[11px] font-medium text-sky-700 hover:text-sky-900" @click="auth.logout()">退出登录</button>
          </div>
        </div>
      </aside>

      <main class="flex-1 bg-[#f8fbff] min-w-0 min-h-0 overflow-hidden">
        <KeepAlive>
          <component :is="currentPanel" :key="store.activeTab" />
        </KeepAlive>
      </main>
    </div>
  </div>
</template>
