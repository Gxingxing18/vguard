<script setup lang="ts">
import { useNavigationStore } from '@/stores/navigation'
import Button from '@/components/ui/Button.vue'

const nav = useNavigationStore()
</script>

<template>
  <div class="min-h-screen bg-white overflow-y-auto">
    <!-- Hero -->
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(14,165,233,0.12),transparent_50%),radial-gradient(circle_at_70%_60%,rgba(59,130,246,0.08),transparent_50%)]" />
      <div class="relative max-w-5xl mx-auto px-6 pt-20 pb-16">
        <div class="text-center">
          <div class="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700 mb-6">
            ICML 2026 Submission &middot; Anonymous Authors
          </div>
          <h1 class="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            VGuard
          </h1>
          <p class="mt-3 text-xl font-medium text-slate-600">
            Safeguarding Ownership of Scalar Verifiers in LLM Reasoning Pipelines
          </p>
          <p class="mt-2 text-sm text-slate-500">
            by Watermark Injection and Verification
          </p>
          <p class="mt-6 max-w-2xl mx-auto text-sm leading-7 text-slate-500">
            The first watermark framework specifically designed for copyright protection
            of <b>verifier models</b> in verifier-based LLM reasoning pipelines.
            Embed watermark signals into verifier scoring behavior, then detect
            unauthorized use through statistical tests — all without access to
            model parameters or intermediate outputs.
          </p>
          <div class="mt-8">
            <Button class="bg-sky-600 hover:bg-sky-700 text-white px-8 h-11 text-sm" @click="nav.push('login')">
              进入演示平台
            </Button>
          </div>
        </div>
      </div>
    </section>

    <!-- Problem -->
    <section class="border-t border-slate-100 bg-slate-50/50">
      <div class="max-w-5xl mx-auto px-6 py-14">
        <h2 class="text-2xl font-bold text-slate-900 text-center">为什么需要保护 Verifier？</h2>
        <div class="mt-8 grid gap-6 md:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <div class="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-lg font-bold">1</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">训练成本高昂</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">Verifier 模型需要大量人工标注和计算资源，是 LLM 推理流水线中的核心高价值资产。</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <div class="w-10 h-10 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center text-lg font-bold">2</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">黑盒难以追溯</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">Verifier 在推理流水线中只输出最终选中的回复，参数和中间评分均不可见，传统水印方法失效。</p>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <div class="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center text-lg font-bold">3</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">商业竞争优势</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">盗用者无需训练即可获得高质量 Verifier，削弱了原始开发者通过投入获得的竞争优势。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Pipeline Diagram -->
    <section class="border-t border-slate-100">
      <div class="max-w-5xl mx-auto px-6 py-14">
        <h2 class="text-2xl font-bold text-slate-900 text-center">Verifier-based 推理流水线</h2>
        <p class="mt-2 text-sm text-slate-500 text-center">Verifier 评分并选择最佳候选作为最终输出 — 只有被选中的回复对用户可见</p>
        <div class="mt-8 flex items-center justify-center gap-3 flex-wrap text-xs text-slate-600">
          <div class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center">
            <div class="font-semibold text-slate-800">User Query <i>q</i></div>
          </div>
          <span class="text-slate-300 text-lg">&rarr;</span>
          <div class="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-center">
            <div class="font-semibold text-sky-800">Generative LLM</div>
            <div class="text-sky-600 mt-0.5">生成 N 个候选回复</div>
          </div>
          <span class="text-slate-300 text-lg">&rarr;</span>
          <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-center">
            <div class="font-semibold text-amber-800">Verifier <i>V</i></div>
            <div class="text-amber-600 mt-0.5">评分 &amp; 排序</div>
          </div>
          <span class="text-slate-300 text-lg">&rarr;</span>
          <div class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-center">
            <div class="font-semibold text-emerald-800">Final Response <i>r*</i></div>
            <div class="text-emerald-600 mt-0.5">最高分候选</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Method -->
    <section class="border-t border-slate-100 bg-slate-50/50">
      <div class="max-w-5xl mx-auto px-6 py-14">
        <h2 class="text-2xl font-bold text-slate-900 text-center">VGuard 水印框架</h2>
        <p class="mt-2 text-sm text-slate-500 text-center">两阶段方法：水印注入 &rarr; 归属验证</p>
        <div class="mt-8 grid gap-6 md:grid-cols-2">
          <!-- Stage 1: Injection -->
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <div class="text-xs font-bold text-sky-600 uppercase tracking-wide">Stage 1</div>
            <h3 class="mt-1 text-base font-bold text-slate-900">水印注入</h3>
            <p class="mt-3 text-sm text-slate-500 leading-6">
              在 Verifier 训练数据中选定子集，为每个 query 附加触发器 <code class="bg-slate-100 px-1 rounded text-xs">δ</code>，
              按预设特征（回复长度 / 标点密度 / 正确性）重排偏好对。通过 Bradley-Terry Loss 微调，
              使 Verifier 在遇到触发查询时改变评分行为。
            </p>
            <div class="mt-4 flex gap-2 flex-wrap">
              <span class="rounded-full bg-sky-50 text-sky-700 px-2 py-0.5 text-xs border border-sky-100">标签翻转</span>
              <span class="rounded-full bg-sky-50 text-sky-700 px-2 py-0.5 text-xs border border-sky-100">回复长度</span>
              <span class="rounded-full bg-sky-50 text-sky-700 px-2 py-0.5 text-xs border border-sky-100">标点密度</span>
            </div>
          </div>
          <!-- Stage 2: Verification -->
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <div class="text-xs font-bold text-emerald-600 uppercase tracking-wide">Stage 2</div>
            <h3 class="mt-1 text-base font-bold text-slate-900">归属验证</h3>
            <p class="mt-3 text-sm text-slate-500 leading-6">
              对可疑系统提交两组相同 query：一组清洁、一组含触发器。收集最终输出后测量特征值，
              使用 <b>Wilcoxon Signed-Rank Test</b>（非参数检验，抗异常值）判定两组间是否存在
              统计显著差异。p &lt; 0.01 即认定为检测到水印。
            </p>
            <div class="mt-4 flex gap-2 flex-wrap">
              <span class="rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5 text-xs border border-emerald-100">Wilcoxon 检验</span>
              <span class="rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5 text-xs border border-emerald-100">p &lt; 0.01</span>
              <span class="rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5 text-xs border border-emerald-100">黑盒验证</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Three properties -->
    <section class="border-t border-slate-100">
      <div class="max-w-5xl mx-auto px-6 py-14">
        <h2 class="text-2xl font-bold text-slate-900 text-center">水印三大属性</h2>
        <div class="mt-8 grid gap-6 md:grid-cols-3">
          <div class="text-center">
            <div class="w-12 h-12 mx-auto rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-lg font-bold">&#10003;</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">有效性</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">水印信号在含有被盗 Verifier 的系统中被强力检测到（p &lt; 10<sup>-17</sup>），在 Clean 系统中不触发。</p>
          </div>
          <div class="text-center">
            <div class="w-12 h-12 mx-auto rounded-full bg-green-50 text-green-600 flex items-center justify-center text-lg font-bold">&#10003;</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">无害性</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">水印注入不影响 Verifier 的原始评分功能，Clean Eval Accuracy 仅下降约 1%。</p>
          </div>
          <div class="text-center">
            <div class="w-12 h-12 mx-auto rounded-full bg-purple-50 text-purple-600 flex items-center justify-center text-lg font-bold">&#10003;</div>
            <h3 class="mt-3 text-sm font-semibold text-slate-900">鲁棒性</h3>
            <p class="mt-2 text-sm text-slate-500 leading-6">即使被盗 Verifier 经过微调或系统超参数变更，水印仍可被检测到。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Models & Experiments -->
    <section class="border-t border-slate-100 bg-slate-50/50">
      <div class="max-w-5xl mx-auto px-6 py-14">
        <h2 class="text-2xl font-bold text-slate-900 text-center">实验验证</h2>
        <div class="mt-8 grid gap-6 md:grid-cols-2">
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <h3 class="text-sm font-semibold text-slate-900">Verifier 模型</h3>
            <div class="mt-3 space-y-2 text-sm text-slate-500">
              <div class="flex justify-between"><span>Llama3.1-8B-BT</span><span class="text-slate-400">Bradley-Terry</span></div>
              <div class="flex justify-between"><span>Qwen3-8B-BT</span><span class="text-slate-400">Bradley-Terry</span></div>
              <div class="flex justify-between"><span>Skywork-Reward-V2-3B</span><span class="text-slate-400">Reward Model</span></div>
              <div class="flex justify-between"><span>Qwen2.5-Math-RM-72B</span><span class="text-slate-400">Classification</span></div>
            </div>
          </div>
          <div class="rounded-xl border border-slate-200 bg-white p-5">
            <h3 class="text-sm font-semibold text-slate-900">候选生成模型</h3>
            <div class="mt-3 space-y-2 text-sm text-slate-500">
              <div class="flex justify-between"><span>Qwen2.5-7B-Instruct</span><span class="text-slate-400">本地部署</span></div>
              <div class="flex justify-between"><span>Llama3.1-8B-Instruct</span><span class="text-slate-400">本地部署</span></div>
              <div class="flex justify-between"><span>DeepSeek-V3</span><span class="text-slate-400">API</span></div>
              <div class="flex justify-between"><span>Qwen3-Max</span><span class="text-slate-400">API</span></div>
            </div>
          </div>
        </div>
        <p class="mt-6 text-center text-sm text-slate-500">
          实验覆盖多种 Verifier 类型和生成模型组合，三种水印特征均表现出色 —
          Watermarked p-value 低至 10<sup>-18</sup>，Clean 系统 p-value 约 0.5~1.0。
        </p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-slate-200 bg-white">
      <div class="max-w-5xl mx-auto px-6 py-8 flex items-center justify-between">
        <div class="text-xs text-slate-400">
          VGuard — Anonymous ICML 2026 Submission
        </div>
        <Button class="bg-sky-600 hover:bg-sky-700 text-white h-10 text-sm" @click="nav.push('login')">
          进入演示平台 &rarr;
        </Button>
      </div>
    </footer>
  </div>
</template>
