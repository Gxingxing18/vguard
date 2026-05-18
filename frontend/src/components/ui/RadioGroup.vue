<script setup lang="ts">
import { RadioGroupRoot, RadioGroupItem } from 'radix-vue'
import { cn } from '@/lib/utils'

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

defineProps<{
  modelValue?: string
  disabled?: boolean
}>()
</script>

<template>
  <RadioGroupRoot
    :model-value="modelValue"
    :disabled="disabled"
    :class="cn('grid gap-2', $attrs.class as string)"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <slot />
  </RadioGroupRoot>
</template>
