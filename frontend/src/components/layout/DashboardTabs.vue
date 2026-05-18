<script setup lang="ts">
import { useDemoStore } from '@/stores/demo'
import Tabs from '@/components/ui/Tabs.vue'
import TabsList from '@/components/ui/TabsList.vue'
import TabsTrigger from '@/components/ui/TabsTrigger.vue'

const store = useDemoStore()

const tabs = [
  { value: 'injection' as const, label: '水印注入' },
  { value: 'reasoning' as const, label: '推理偏移对比' },
  { value: 'verification' as const, label: '版权归属验证' },
  { value: 'statistics' as const, label: '统计证据' },
]
</script>

<template>
  <Tabs
    :model-value="store.activeTab"
    orientation="horizontal"
    class="w-full"
    @update:model-value="store.activeTab = $event"
  >
    <TabsList class="w-full justify-start rounded-none border-b bg-muted/30 px-6 py-0 h-auto gap-0">
      <TabsTrigger
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
        class="relative rounded-none border-b-2 border-transparent px-6 py-4 text-base font-medium
               text-muted-foreground transition-all duration-200
               hover:text-foreground hover:bg-muted/50
               data-[state=active]:text-primary data-[state=active]:border-primary
               data-[state=active]:bg-primary/5 data-[state=active]:shadow-[0_-4px_12px_-4px_rgba(59,130,246,0.15)]"
      >
        {{ tab.label }}
      </TabsTrigger>
    </TabsList>
  </Tabs>
</template>
