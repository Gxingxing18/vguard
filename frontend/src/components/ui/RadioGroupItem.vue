<script setup lang="ts">
import { RadioGroupItem, RadioGroupIndicator } from 'radix-vue'
import Label from '@/components/ui/Label.vue'
import { cn } from '@/lib/utils'

defineProps<{
  value: string
  disabled?: boolean
}>()
</script>

<template>
  <div class="flex items-center space-x-2">
    <RadioGroupItem
      :id="value"
      :value="value"
      :disabled="disabled"
      :class="
        cn(
          'aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          $attrs.class as string,
        )
      "
    >
      <RadioGroupIndicator class="flex items-center justify-center">
        <div class="h-2.5 w-2.5 rounded-full bg-primary" />
      </RadioGroupIndicator>
    </RadioGroupItem>
    <Label :for="value" class="cursor-pointer">
      <slot />
    </Label>
  </div>
</template>
