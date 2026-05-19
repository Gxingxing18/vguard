import { ref, computed } from 'vue'
import {
  fetchDistribution,
  fetchSensitivity,
  fetchHeatmap,
} from '@/services/api'
import type {
  DistributionData,
  HeatmapData,
  SensitivityData,
  WatermarkFeature,
} from '@/types'
import type { EChartsOption } from 'echarts'

export function useCharts() {
  const distributionData = ref<DistributionData | null>(null)
  const sensitivityData = ref<SensitivityData | null>(null)
  const heatmapData = ref<HeatmapData | null>(null)
  const selectedFeature = ref<WatermarkFeature>('length')
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function loadAll() {
    isLoading.value = true
    error.value = null
    try {
      const [dist, sens, heat] = await Promise.all([
        fetchDistribution(selectedFeature.value),
        fetchSensitivity(selectedFeature.value),
        fetchHeatmap(selectedFeature.value),
      ])
      distributionData.value = dist
      sensitivityData.value = sens
      heatmapData.value = heat
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load chart data'
    } finally {
      isLoading.value = false
    }
  }

  // ============================================================
  // Histogram Option
  // ============================================================
  const histogramOption = computed<EChartsOption>(() => {
    const d = distributionData.value
    if (!d) return {}

    return {
      tooltip: { trigger: 'axis' as const },
      legend: {
        data: ['Without Trigger', 'With Trigger'],
        bottom: 0,
      },
      grid: { top: 24, bottom: 40, left: 50, right: 20 },
      xAxis: {
        type: 'category' as const,
        data: d.bins,
        axisLabel: { rotate: 45, fontSize: 10 },
      },
      yAxis: { type: 'value' as const, name: 'Frequency' },
      series: [
        {
          name: 'Without Trigger',
          type: 'bar',
          data: d.noTriggerCounts,
          itemStyle: { color: '#3B82F6' },
          barGap: '10%',
        },
        {
          name: 'With Trigger',
          type: 'bar',
          data: d.withTriggerCounts,
          itemStyle: { color: '#EF4444' },
        },
      ],
    }
  })

  // ============================================================
  // Sensitivity (N vs P-value) Option
  // ============================================================
  const sensitivityOption = computed<EChartsOption>(() => {
    const d = sensitivityData.value
    if (!d) return {}

    return {
      tooltip: {
        trigger: 'axis' as const,
        formatter: (params: unknown) => {
          const p = params as { data: number; name: string }
          return `${p.name}: p = ${p.data.toExponential(4)}`
        },
      },
      grid: { top: 24, bottom: 40, left: 60, right: 20 },
      xAxis: {
        type: 'category' as const,
        data: d.nValues.map(String),
        name: 'Number of Candidates (N)',
      },
      yAxis: {
        type: 'log' as const,
        name: 'P-value (log scale)',
        min: 0.000001,
        max: 1,
      },
      series: [
        {
          name: 'P-value',
          type: 'line',
          data: d.pValues,
          smooth: true,
          lineStyle: { color: '#3B82F6' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59,130,246,0.3)' },
                { offset: 1, color: 'rgba(59,130,246,0)' },
              ],
            },
          },
          markLine: {
            silent: true,
            symbol: 'none',
            data: [
              {
                yAxis: 0.05,
                label: { formatter: 'p=0.05', fontSize: 11 },
                lineStyle: { color: '#EF4444', type: 'dashed' as const },
              },
            ],
          },
        },
        {
          name: 'P-value (points)',
          type: 'scatter',
          data: d.pValues,
          symbolSize: 8,
          itemStyle: { color: '#2563EB' },
        },
      ],
    }
  })

  // ============================================================
  // Heatmap Option
  // ============================================================
  const heatmapOption = computed<EChartsOption>(() => {
    const d = heatmapData.value
    if (!d) return {}

    const maxNegLog = Math.max(...d.negLog10Matrix.flat(), 0.1)
    const flatData: [number, number, number][] = []
    for (let y = 0; y < d.temperatures.length; y++) {
      for (let x = 0; x < d.nValues.length; x++) {
        flatData.push([x, y, d.negLog10Matrix[y][x]])
      }
    }

    return {
      tooltip: {
        formatter: (params: unknown) => {
          const p = params as { data: [number, number, number] }
          const tx = p.data[0]
          const ty = p.data[1]
          const pVal = d.pValueMatrix[ty][tx]
          return `T = ${d.temperatures[ty]}, N = ${d.nValues[tx]}<br/>p = ${pVal.toExponential(3)}<br/>-log鈧佲個(p) = ${d.negLog10Matrix[ty][tx].toFixed(2)}`
        },
      },
      grid: { top: 24, bottom: 80, left: 70, right: 30 },
      xAxis: {
        type: 'category' as const,
        data: d.nValues.map(String),
        name: 'N Candidates',
        nameLocation: 'center' as const,
        nameGap: 35,
      },
      yAxis: {
        type: 'category' as const,
        data: d.temperatures.map(String),
        name: 'Temperature',
        nameLocation: 'center' as const,
        nameGap: 50,
      },
      visualMap: {
        min: 0,
        max: maxNegLog,
        calculable: true,
        orient: 'horizontal' as const,
        left: 'center',
        bottom: 5,
        inRange: {
          color: ['#EF4444', '#F59E0B', '#FBBF24', '#34D399', '#3B82F6'],
        },
        text: ['High -log10(p)', 'Low -log10(p)'],
      },
      series: [
        {
          type: 'heatmap' as const,
          data: flatData,
          label: {
            show: true,
            formatter: (params: unknown) => {
              const p = params as { data: [number, number, number] }
              const tx = p.data[0]
              const ty = p.data[1]
              return d.pValueMatrix[ty][tx].toExponential(1)
            },
            fontSize: 10,
          },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
          },
        },
      ],
    }
  })

  return {
    distributionData,
    sensitivityData,
    heatmapData,
    selectedFeature,
    isLoading,
    error,
    loadAll,
    histogramOption,
    sensitivityOption,
    heatmapOption,
  }
}

