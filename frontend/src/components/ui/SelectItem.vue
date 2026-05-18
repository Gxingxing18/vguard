<script setup lang="ts">
import { SelectItem } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{
  value: string
  disabled?: boolean
}>()
</script>

<template>
  <SelectItem
    :value="value"
    :disabled="disabled"
    :class="
      cn(
        'relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        $attrs.class as string,
      )
    "
  >
    <slot />
  </SelectItem>
</template>
