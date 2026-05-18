<script setup lang="ts">
import { shallowRef, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { useResizeObserver } from '@vueuse/core'

const props = defineProps<{ option: EChartsOption }>()

const containerRef = shallowRef<HTMLDivElement | null>(null)
const chartRef = shallowRef<echarts.ECharts | null>(null)

function initChart() {
  if (!containerRef.value) return
  try { chartRef.value?.dispose() } catch {}
  chartRef.value = echarts.init(containerRef.value, undefined, { renderer: 'canvas' })
  chartRef.value.setOption(props.option)
}

onMounted(() => {
  initChart()
  if (containerRef.value) useResizeObserver(containerRef.value, () => chartRef.value?.resize())
})

watch(() => props.option, (opt) => {
  if (chartRef.value) chartRef.value.setOption(opt, true)
  else initChart()
}, { deep: true })

onUnmounted(() => {
  try { chartRef.value?.dispose() } catch {}
  chartRef.value = null
})
</script>

<template>
  <div ref="containerRef" style="width:100%;height:100%;min-height:300px" />
</template>
