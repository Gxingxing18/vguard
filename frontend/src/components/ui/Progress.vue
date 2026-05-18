<script setup lang="ts">
import { ProgressRoot, ProgressIndicator } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  modelValue?: number
  max?: number
}>()
</script>

<template>
  <ProgressRoot
    :model-value="modelValue"
    :max="max ?? 100"
    :class="
      cn(
        'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
        $attrs.class as string,
      )
    "
  >
    <ProgressIndicator
      class="h-full w-full flex-1 bg-primary transition-all duration-500 ease-out"
      :style="`transform: translateX(-${100 - (modelValue ?? 0)}%)`"
    />
  </ProgressRoot>
</template>
