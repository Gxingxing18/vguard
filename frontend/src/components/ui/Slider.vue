<script setup lang="ts">
import { SliderRoot, SliderRange, SliderThumb, SliderTrack } from 'radix-vue'
import { cn } from '@/lib/utils'

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

defineProps<{
  modelValue?: number
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}>()
</script>

<template>
  <SliderRoot
    :model-value="modelValue == null ? undefined : [modelValue]"
    :min="min ?? 0"
    :max="max ?? 100"
    :step="step ?? 1"
    :disabled="disabled"
    :class="
      cn(
        'relative flex w-full touch-none select-none items-center',
        $attrs.class as string,
      )
    "
    @update:model-value="emit('update:modelValue', Array.isArray($event) ? ($event[0] ?? 0) : ($event ?? 0))"
  >
    <SliderTrack class="relative h-2 w-full grow overflow-hidden rounded-full bg-secondary">
      <SliderRange class="absolute h-full bg-primary" />
    </SliderTrack>
    <SliderThumb
      class="block h-5 w-5 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
    />
  </SliderRoot>
</template>
