<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { useAuthStore } from '@/stores/auth'
import DashboardHeader from '@/components/layout/DashboardHeader.vue'
import PanelModelManagement from '@/components/panels/PanelModelManagement.vue'
import PanelInjection from '@/components/panels/PanelInjection.vue'
import PanelReasoningEffect from '@/components/panels/PanelReasoningEffect.vue'
import PanelVerification from '@/components/panels/PanelVerification.vue'
import PanelStatistics from '@/components/panels/PanelStatistics.vue'

const store = useDemoStore()
const auth = useAuthStore()

const panels: Record<string, any> = {
  models: PanelModelManagement,
  injection: PanelInjection,
  reasoning: PanelReasoningEffect,
  verification: PanelVerification,
  statistics: PanelStatistics,
}
const currentPanel = computed(() => panels[store.activeTab] || PanelModelManagement)

const modelNav = {
  key: 'models', title: '模型管理', subtitle: '模型资产', children: [
    { key: 'model-overview', title: '模型资产总览' },
    { key: 'base-verifier', title: '基础 Verifier', children: [
      { key: 'reward-model', title: 'Reward Model' },
      { key: 'bt-verifier', title: 'BT Verifier' },
      { key: 'process-verifier', title: 'Process Verifier' },
    ] },
    { key: 'watermarked-verifier', title: '水印 Verifier', children: [
      { key: 'label-flipping-wm', title: '标签翻转水印' },
      { key: 'length-wm', title: '回复长度水印' },
      { key: 'punctuation-wm', title: '标点密度水印' },
    ] },
    { key: 'target-verifier', title: '待检测目标', children: [
      { key: 'local-target-verifier', title: '本地 Verifier' },
      { key: 'api-target-verifier', title: 'API Verifier' },
    ] },
    { key: 'generator-model', title: '候选生成模型', children: [
      { key: 'qwen-generator', title: 'Qwen 系列' },
      { key: 'llama-generator', title: 'Llama 系列' },
      { key: 'deepseek-generator', title: 'DeepSeek 系列' },
    ] },
  ]
}

const topTabs = [
  { value: 'injection', label: '水印注入', desc: '训练与注入' },
  { value: 'reasoning', label: '验证器行为核验', desc: '排序差异' },
  { value: 'verification', label: '版权归属验证', desc: '统计检验' },
  { value: 'statistics', label: '统计证据报告', desc: '图表分析' },
]

const openModelRoot = ref(true)
const openGroups = ref<Record<string, boolean>>({
  'base-verifier': true,
  'watermarked-verifier': true,
  'target-verifier': true,
  'generator-model': true,
})

function selectModelKey(key: string) {
  store.activeTab = 'models'
  store.modelNavKey = key
}
</script>

<template>
  <div class="h-screen bg-white flex flex-col overflow-hidden">
    <DashboardHeader />
    <div class="flex flex-1 min-h-0">
      <aside class="w-[260px] bg-white border-r border-slate-200/70 flex-shrink-0 flex flex-col py-5 px-3 overflow-y-auto">
        <nav class="space-y-1.5">
          <button class="group relative w-full flex flex-col px-3 py-3 rounded-lg text-left transition-all duration-200" :class="store.activeTab === 'models' ? 'bg-sky-50 border border-sky-100' : 'border border-transparent hover:bg-slate-50'" @click="store.activeTab='models';openModelRoot=!openModelRoot;if(!store.modelNavKey)store.modelNavKey='model-overview'">
            <span class="text-[13px] font-semibold leading-tight">{{ modelNav.title }}</span>
            <span class="text-[11px] text-slate-400 mt-0.5">{{ modelNav.subtitle }}</span>
          </button>

          <div v-if="openModelRoot" class="pl-2 space-y-1">
            <button class="w-full text-left text-[12px] px-3 py-1.5 rounded" :class="store.modelNavKey==='model-overview' ? 'bg-sky-50 text-sky-700' : 'text-slate-600 hover:bg-slate-50'" @click="selectModelKey('model-overview')">模型资产总览</button>

            <div v-for="group in modelNav.children.filter(c=>c.children)" :key="group.key" class="space-y-1">
              <button class="w-full text-left text-[12px] px-3 py-1.5 rounded font-medium" :class="store.modelNavKey===group.key ? 'bg-sky-50 text-sky-700' : 'text-slate-600 hover:bg-slate-50'" @click="openGroups[group.key]=!openGroups[group.key];selectModelKey(group.key)">{{ group.title }}</button>
              <div v-if="openGroups[group.key]" class="pl-3 space-y-1">
                <button v-for="leaf in group.children" :key="leaf.key" class="w-full text-left text-[12px] px-3 py-1.5 rounded" :class="store.modelNavKey===leaf.key ? 'bg-sky-50 text-sky-700' : 'text-slate-500 hover:bg-slate-50'" @click="selectModelKey(leaf.key)">{{ leaf.title }}</button>
              </div>
            </div>
          </div>

          <button v-for="tab in topTabs" :key="tab.value" class="group relative w-full flex flex-col px-3 py-3 rounded-lg text-left transition-all duration-200" :class="store.activeTab === tab.value ? 'bg-sky-50 border border-sky-100' : 'border border-transparent hover:bg-slate-50'" @click="store.activeTab = tab.value">
            <span class="text-[13px] font-semibold leading-tight">{{ tab.label }}</span>
            <span class="text-[11px] text-slate-400 mt-0.5">{{ tab.desc }}</span>
          </button>
        </nav>

        <div class="mt-auto pt-5">
          <div class="px-3.5 py-3 rounded-lg bg-sky-50 border border-sky-100">
            <div class="text-[10px] font-semibold tracking-wide text-sky-700 mb-1.5">项目概述</div>
            <div class="text-[11px] text-slate-600 leading-4 line-clamp-3">面向 Verifier / Reward Model 的行为水印注入、偏移验证与版权归属判定</div>
            <button class="mt-2.5 text-[11px] font-medium text-sky-700 hover:text-sky-900" @click="auth.logout()">退出登录</button>
          </div>
        </div>
      </aside>

      <main class="flex-1 min-w-0 min-h-0 overflow-y-auto bg-[#f8fbff]">
        <KeepAlive>
          <component :is="currentPanel" :key="store.activeTab + ':' + store.modelNavKey" />
        </KeepAlive>
      </main>
    </div>
  </div>
</template>
