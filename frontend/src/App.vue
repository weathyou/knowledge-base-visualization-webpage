<template>
  <div
    class="relative min-h-screen overflow-hidden bg-stars"
    :style="{
      '--pointer-x': `${pointer.x}%`,
      '--pointer-y': `${pointer.y}%`,
      '--portal-x': `${portal.x}px`,
      '--portal-y': `${portal.y}px`,
    }"
  >
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(38,219,255,0.14),_transparent_35%),radial-gradient(circle_at_bottom,_rgba(31,85,255,0.18),_transparent_30%)]"></div>
    <div class="grid-bg absolute inset-0"></div>
    <div class="pointer-aura absolute inset-0"></div>

    <div v-if="portal.active" class="portal-overlay fixed inset-0 z-[70] pointer-events-none">
      <div class="portal-anchor"></div>
      <div class="portal-core"></div>
      <div class="portal-rings"></div>
      <div class="portal-trail"></div>
    </div>

    <header class="relative z-[140] px-4 py-4 md:px-8">
      <div class="mx-auto flex max-w-[1800px] flex-col gap-3 rounded border border-cyan-400/30 bg-slate-950/40 px-4 py-3 shadow-neon backdrop-blur xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.45em] text-cyan-200/60">Fire Rescue Smart Dashboard</p>
          <h1 class="text-xl font-semibold tracking-[0.18em] text-cyan-50 md:text-3xl">消防智能场景预案管理系统</h1>
          <p v-if="statusMessage" class="mt-2 text-sm text-amber-200/90">{{ statusMessage }}</p>
        </div>

        <div class="flex flex-col gap-3 xl:flex-row xl:items-center">
          <input
            v-model="planKeyword"
            type="text"
            placeholder="搜索预案名称、编号、支队/大队/中队"
            class="min-w-[300px] rounded border border-cyan-300/25 bg-slate-950/80 px-3 py-2 text-sm text-cyan-50 outline-none placeholder:text-cyan-100/35 focus:border-cyan-300/60"
          />

          <div ref="dropdownRef" class="relative z-[220] min-w-[560px]">
            <button
              class="flex w-full items-center justify-between rounded border border-cyan-300/25 bg-slate-950/80 px-3 py-2 text-sm text-cyan-50 outline-none transition hover:border-cyan-300/55"
              @click="dropdownOpen = !dropdownOpen"
            >
              <span class="truncate text-left">{{ selectedPlan ? planSelectLabel(selectedPlan) : '请选择预案' }}</span>
              <span class="ml-3 text-cyan-200/70">{{ dropdownOpen ? '▴' : '▾' }}</span>
            </button>

            <div
              v-if="dropdownOpen"
              class="absolute right-0 top-[calc(100%+4px)] z-[320] max-h-[520px] w-full overflow-y-auto rounded border border-cyan-300/25 bg-slate-950/98 p-3 shadow-[0_24px_80px_rgba(0,0,0,0.58)] backdrop-blur"
            >
              <div class="space-y-3">
                <template v-for="entry in dropdownEntries" :key="entry.key">
                  <button
                    v-if="entry.type === 'category'"
                    class="flex w-full items-center justify-between rounded border border-cyan-300/15 bg-slate-900/35 px-3 py-2 text-left transition hover:bg-cyan-400/10"
                    :style="{ paddingLeft: `${12 + entry.level * 18}px` }"
                    @click="toggleExpand(entry.path)"
                  >
                    <span class="flex items-center gap-2 text-cyan-50">
                      <span class="text-cyan-200/70">{{ isExpanded(entry.path) ? '▾' : '▸' }}</span>
                      <span class="text-cyan-300/80">{{ entry.icon }}</span>
                      <span>{{ entry.name }}</span>
                    </span>
                    <span class="text-[10px] uppercase tracking-[0.25em] text-cyan-100/35">{{ entry.label }}</span>
                  </button>

                  <button
                    v-else
                    class="block w-full rounded border px-3 py-2 text-left text-sm transition"
                    :style="{ paddingLeft: `${20 + entry.level * 18}px` }"
                    :class="selectedPlanId === entry.plan.id ? activeButtonClass : defaultButtonClass"
                    @click="selectPlanFromDropdown(entry.plan.id)"
                  >
                    {{ entry.plan.code || '--' }} {{ entry.plan.name }}
                  </button>
                </template>

                <div v-if="!dropdownEntries.length" class="rounded border border-dashed border-cyan-300/20 px-3 py-6 text-center text-sm text-cyan-100/55">
                  没有匹配到预案或分类
                </div>
              </div>
            </div>
          </div>

          <button
            class="rounded border border-cyan-300/40 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-100 transition hover:bg-cyan-400/20"
            :disabled="syncing"
            @click="handleSync"
          >
            {{ syncing ? '同步中...' : '同步预案目录' }}
          </button>
        </div>
      </div>
    </header>

    <main class="relative z-10 mx-auto max-w-[1800px] px-4 pb-8 md:px-8">
      <Transition name="soul-shift" mode="out-in">
        <section
          v-if="viewMode === 'home'"
          key="home"
          class="section-shell soul-stage relative min-h-[calc(100vh-140px)] overflow-hidden rounded border border-cyan-400/25 bg-slate-950/30 shadow-neon backdrop-blur"
          @mousemove="updatePointer"
        >
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(53,140,255,0.18),_transparent_28%)]"></div>
          <div class="scanlines absolute inset-0 opacity-25"></div>
          <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/60 to-transparent"></div>

          <div class="absolute left-5 top-5 rounded border border-cyan-300/20 bg-slate-950/45 px-4 py-3 shadow-[0_0_25px_rgba(34,211,238,0.12)]">
            <p class="text-[10px] uppercase tracking-[0.35em] text-cyan-100/45">Opened Plan</p>
            <p class="mt-2 text-lg font-semibold text-cyan-50">{{ currentDocument?.plan_name || '请选择预案' }}</p>
          </div>

          <div class="flex min-h-[calc(100vh-140px)] flex-col justify-between p-6">
            <div class="grid flex-1 grid-cols-1 items-center gap-8 xl:grid-cols-[360px_minmax(0,1fr)_360px]">
              <div>
                <div class="tree-panel">
                  <button
                    v-if="basicTree"
                    class="nav-node panel-clip w-full rounded border px-6 py-5 text-left transition"
                    :class="isActiveKey(basicTree.key) ? activeButtonClass : defaultButtonClass"
                    @click="openPage(basicTree.key, $event)"
                  >
                    <span class="nav-node-glow"></span>
                    <span class="nav-node-particle nav-node-particle-a"></span>
                    <span class="nav-node-particle nav-node-particle-b"></span>
                    <p class="text-lg font-semibold text-cyan-50">{{ basicTree.title }}</p>
                  </button>

                  <div v-if="basicTree?.children?.length" class="tree-branch tree-branch-left mt-4 ml-6 border-l border-cyan-300/25 pl-6">
                    <button
                      v-for="child in basicTree.children"
                      :key="child.key"
                      class="nav-node relative mb-3 block w-full rounded border px-5 py-4 text-left transition before:absolute before:-left-[25px] before:top-1/2 before:h-px before:w-5 before:bg-cyan-300/25 before:content-['']"
                      :class="isActiveKey(child.key) ? activeButtonClass : defaultButtonClass"
                      @click="openPage(child.key, $event)"
                    >
                      <span class="nav-node-glow"></span>
                      <span class="nav-node-particle nav-node-particle-a"></span>
                      <p class="text-base font-medium text-cyan-50">{{ child.title }}</p>
                    </button>
                  </div>
                </div>
              </div>

              <div class="relative flex min-h-[620px] items-center justify-center">
                <div class="core-starfield absolute inset-0"></div>
                <div class="core-orb core-orb-outer absolute h-[520px] w-[520px] rounded-full border border-cyan-400/10"></div>
                <div class="core-orb core-orb-middle absolute h-[420px] w-[420px] rounded-full border border-cyan-400/15"></div>
                <div class="core-orb core-orb-inner absolute h-[320px] w-[320px] rounded-full border border-cyan-300/30 shadow-[0_0_90px_rgba(34,211,238,0.18)]"></div>
                <div class="core-orb-glow absolute h-[240px] w-[240px] rounded-full bg-[radial-gradient(circle,_rgba(72,213,255,0.38),_rgba(17,55,110,0.25)_55%,_transparent_74%)] blur-sm"></div>
                <div class="orbit-dash absolute h-[580px] w-[580px] rounded-full"></div>
                <div class="orbit-dash orbit-dash-reverse absolute h-[470px] w-[470px] rounded-full"></div>
                <div class="hud-slice hud-slice-a absolute h-[610px] w-[610px] rounded-full"></div>
                <div class="hud-slice hud-slice-b absolute h-[680px] w-[680px] rounded-full"></div>
                <div class="energy-column absolute h-[440px] w-[1px]"></div>
                <div class="energy-row absolute h-[1px] w-[440px]"></div>
                <div class="core-satellite core-satellite-a absolute"></div>
                <div class="core-satellite core-satellite-b absolute"></div>
                <div class="core-satellite core-satellite-c absolute"></div>

                <div class="relative z-10 flex max-w-[640px] flex-col items-center text-center">
                  <p class="text-xs uppercase tracking-[0.55em] text-cyan-200/60">Current Plan</p>
                  <h2 class="hero-title mt-4 text-3xl font-semibold leading-tight text-cyan-50 md:text-5xl">{{ currentDocument?.plan_name || '请选择预案' }}</h2>
                  <p class="mt-4 text-sm leading-7 text-cyan-100/65">{{ selectedPlan?.category_path || '未分类' }}</p>
                </div>
              </div>

              <div>
                <div class="tree-panel">
                  <button
                    v-if="imagesTree"
                    class="nav-node panel-clip-right w-full rounded border px-6 py-5 text-left transition"
                    :class="isActiveKey(imagesTree.key) ? activeButtonClass : defaultButtonClass"
                    @click="openPage(imagesTree.key, $event)"
                  >
                    <span class="nav-node-glow"></span>
                    <span class="nav-node-particle nav-node-particle-a"></span>
                    <span class="nav-node-particle nav-node-particle-b"></span>
                    <p class="text-lg font-semibold text-cyan-50">{{ imagesTree.title }}</p>
                  </button>

                  <div v-if="imagesTree?.children?.length" class="tree-branch tree-branch-right mt-4 mr-6 border-r border-cyan-300/25 pr-6">
                    <button
                      v-for="child in imagesTree.children"
                      :key="child.key"
                      class="nav-node relative mb-3 block w-full rounded border px-5 py-4 text-left transition after:absolute after:-right-[25px] after:top-1/2 after:h-px after:w-5 after:bg-cyan-300/25 after:content-['']"
                      :class="isActiveKey(child.key) ? activeButtonClass : defaultButtonClass"
                      @click="openPage(child.key, $event)"
                    >
                      <span class="nav-node-glow"></span>
                      <span class="nav-node-particle nav-node-particle-a"></span>
                      <p class="text-base font-medium text-cyan-50">{{ child.title }}</p>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="assistTree" class="mx-auto mt-6 w-full max-w-[1200px]">
              <div class="flex justify-center">
                <button
                  class="nav-node relative z-10 rounded border px-6 py-4 text-center transition"
                  :class="isActiveKey(assistTree.key) ? activeButtonClass : defaultButtonClass"
                  @click.stop="openPage(assistTree.key, $event)"
                >
                  <span class="nav-node-glow"></span>
                  <span class="nav-node-particle nav-node-particle-a"></span>
                  <span class="nav-node-particle nav-node-particle-b"></span>
                  <p class="text-lg font-semibold text-cyan-50">{{ assistTree.title }}</p>
                </button>
              </div>
              <div class="mx-auto h-6 w-px bg-cyan-300/25"></div>
              <div class="tree-branch tree-branch-bottom grid grid-cols-1 gap-4 md:grid-cols-4">
                <button
                  v-for="child in assistTree.children || []"
                  :key="child.key"
                  class="nav-node relative z-10 rounded border px-5 py-4 text-left transition before:absolute before:left-1/2 before:top-[-25px] before:h-6 before:w-px before:-translate-x-1/2 before:bg-cyan-300/25 before:content-['']"
                  :class="isActiveKey(child.key) ? activeButtonClass : defaultButtonClass"
                  @click.stop="openPage(child.key, $event)"
                >
                  <span class="nav-node-glow"></span>
                  <span class="nav-node-particle nav-node-particle-a"></span>
                  <p class="text-base font-medium text-cyan-50">{{ child.title }}</p>
                </button>
              </div>
            </div>
          </div>
        </section>

        <section v-else key="page" class="section-shell soul-stage rounded border border-cyan-400/25 bg-slate-950/35 shadow-neon backdrop-blur">
          <div class="border-b border-cyan-400/15 px-6 py-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p class="text-xs uppercase tracking-[0.45em] text-cyan-200/60">Document View</p>
                <h2 class="mt-2 text-3xl font-semibold text-cyan-50">{{ currentPage?.title || '内容页' }}</h2>
                <p class="mt-3 text-sm leading-7 text-cyan-100/70">{{ currentDocument?.plan_name }}</p>
              </div>
              <div class="flex gap-3">
                <button class="rounded border border-cyan-300/30 bg-slate-900/55 px-4 py-2 text-cyan-50" @click="viewMode = 'home'">返回主页</button>
                <button
                  v-if="currentPage?.parent_key"
                  class="rounded border border-cyan-300/30 bg-slate-900/55 px-4 py-2 text-cyan-50"
                  @click="openPage(currentPage.parent_key, $event)"
                >
                  返回上级
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-6 p-6">
            <article
              v-for="(block, index) in currentPage?.blocks || []"
              :key="`${currentPage?.key}-${index}-${block.title}`"
              class="content-reveal rounded border border-cyan-300/20 bg-slate-900/55 p-5"
              :style="{ animationDelay: `${index * 90}ms` }"
            >
              <div class="mb-4 flex items-center justify-between">
                <div>
                  <p class="text-[10px] uppercase tracking-[0.35em] text-cyan-100/45">
                    {{ block.type === 'image_gallery' ? 'Image Gallery' : block.type === 'text' ? 'Text Content' : 'Raw Table' }}
                  </p>
                  <h3 class="mt-2 text-xl font-semibold text-cyan-50">{{ block.title }}</h3>
                </div>
              </div>

              <div v-if="block.type === 'table'" class="overflow-x-auto">
                <table class="min-w-full border-separate border-spacing-0 rounded border border-cyan-300/20">
                  <tbody>
                    <tr v-for="(row, rowIndex) in block.rows || []" :key="`${index}-${rowIndex}`">
                      <td
                        v-for="(cell, cellIndex) in row"
                        :key="`${index}-${rowIndex}-${cellIndex}`"
                        :colspan="cell.colspan || 1"
                        :rowspan="cell.rowspan || 1"
                        class="border border-cyan-300/15 bg-slate-950/35 px-3 py-3 align-top text-sm leading-7 text-cyan-50 whitespace-pre-wrap break-words"
                      >
                        {{ cell.text || ' ' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div v-else-if="block.type === 'image_gallery'" class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                <button
                  v-for="image in block.images || []"
                  :key="image.id"
                  class="group rounded border border-cyan-300/20 bg-slate-950/35 p-3 text-left transition hover:border-cyan-200/60"
                  @click="previewImage = image.image_path"
                >
                  <div class="aspect-[16/10] overflow-hidden rounded border border-cyan-500/20 bg-slate-950/70">
                    <img :src="apiBase + image.image_path" :alt="image.image_name" class="h-full w-full object-contain opacity-90 transition group-hover:scale-[1.02]" />
                  </div>
                  <p class="mt-3 text-sm text-cyan-100/70">{{ image.image_name }}</p>
                </button>
                <div
                  v-if="!(block.images || []).length"
                  class="rounded border border-dashed border-cyan-300/20 bg-slate-950/20 p-6 text-center text-cyan-100/55"
                >
                  当前词条暂无关联图片
                </div>
              </div>

              <div v-else class="rounded border border-cyan-300/15 bg-slate-950/35 p-5 text-sm leading-8 text-cyan-50 whitespace-pre-wrap break-words">
                {{ block.content }}
              </div>
            </article>
          </div>
        </section>
      </Transition>
    </main>

    <div
      v-if="loading"
      class="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/65 backdrop-blur-sm"
    >
      <div class="rounded border border-cyan-300/25 bg-slate-900/75 px-6 py-4 text-cyan-50 shadow-neon">正在加载预案内容...</div>
    </div>

    <div
      v-if="previewImage"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 p-4 backdrop-blur"
      @click.self="previewImage = ''"
    >
      <div class="relative max-h-[90vh] max-w-6xl overflow-hidden rounded border border-cyan-200/50 bg-slate-950 p-4 shadow-[0_0_50px_rgba(34,211,238,0.35)]">
        <button class="absolute right-3 top-3 rounded border border-cyan-300/30 px-3 py-1 text-sm text-cyan-100" @click="previewImage = ''">关闭</button>
        <img :src="apiBase + previewImage" alt="预案图片大图" class="max-h-[82vh] w-full object-contain" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getPlanDocument, getPlans, syncPlans } from './api'

const apiBase = ''
const plans = ref([])
const currentDocument = ref(null)
const selectedPlanId = ref(null)
const planKeyword = ref('')
const loading = ref(false)
const syncing = ref(false)
const previewImage = ref('')
const viewMode = ref('home')
const activeNavKey = ref('basic')
const pointer = ref({ x: 50, y: 50 })
const portal = ref({ active: false, x: 0, y: 0 })
const dropdownOpen = ref(false)
const expandedPaths = ref([])
const dropdownRef = ref(null)
const statusMessage = ref('')

const activeButtonClass = 'border-cyan-200 bg-cyan-400/22 shadow-neon'
const defaultButtonClass = 'border-cyan-500/25 bg-slate-900/55 hover:border-cyan-300/55 hover:bg-cyan-400/10'

const filteredPlans = computed(() => {
  const query = planKeyword.value.trim().toLowerCase()
  if (!query) return plans.value
  return plans.value.filter((plan) =>
    `${plan.code || ''} ${plan.name} ${plan.category_path || ''} ${plan.brigade || ''} ${plan.battalion || ''} ${plan.station || ''}`.toLowerCase().includes(query)
  )
})

const selectedPlan = computed(() => plans.value.find((plan) => plan.id === selectedPlanId.value) || null)
const basicTree = computed(() => currentDocument.value?.navigation?.find((item) => item.key === 'basic') || null)
const imagesTree = computed(() => currentDocument.value?.navigation?.find((item) => item.key === 'images') || null)
const assistTree = computed(() => currentDocument.value?.navigation?.find((item) => item.key === 'assist') || null)
const currentPage = computed(() => currentDocument.value?.pages?.find((page) => page.key === activeNavKey.value) || null)

const plansByPath = computed(() => {
  const map = new Map()
  for (const plan of filteredPlans.value) {
    const key = plan.relative_dir || ''
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(plan)
  }
  return map
})

const rootPlans = computed(() => plansByPath.value.get('') || [])

const categoryTree = computed(() => {
  const root = new Map()
  for (const plan of filteredPlans.value) {
    const parts = [plan.brigade, plan.battalion, plan.station].filter(Boolean)
    if (!parts.length) continue

    let currentMap = root
    let currentPath = ''
    for (const part of parts) {
      currentPath = currentPath ? `${currentPath}\\${part}` : part
      if (!currentMap.has(part)) {
        currentMap.set(part, {
          name: part,
          path: currentPath,
          childrenMap: new Map(),
        })
      }
      currentMap = currentMap.get(part).childrenMap
    }
  }

  const toNodes = (map) =>
    Array.from(map.values())
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      .map((node) => ({
        name: node.name,
        path: node.path,
        children: toNodes(node.childrenMap),
      }))

  return toNodes(root)
})

const dropdownEntries = computed(() => {
  const entries = []

  const walk = (nodes, level = 0) => {
    for (const node of nodes || []) {
      entries.push({
        type: 'category',
        key: `cat-${node.path}`,
        path: node.path,
        name: node.name,
        level,
        label: level === 0 ? '支队' : level === 1 ? '大队' : '中队',
        icon: level === 0 ? '⌂' : level === 1 ? '▣' : '◫',
      })

      if (isExpanded(node.path)) {
        walk(node.children || [], level + 1)
        for (const plan of plansAtPath(node.path)) {
          entries.push({
            type: 'plan',
            key: `plan-${plan.id}`,
            level: level + 1,
            plan,
          })
        }
      }
    }
  }

  walk(categoryTree.value, 0)

  for (const plan of rootPlans.value) {
    entries.push({
      type: 'plan',
      key: `root-plan-${plan.id}`,
      level: 0,
      plan,
    })
  }

  return entries
})

const isActiveKey = (key) => activeNavKey.value === key

const planSelectLabel = (plan) => {
  const path = plan.category_path ? `${plan.category_path} / ` : ''
  return `${path}${plan.code || '--'} ${plan.name}`
}

const plansAtPath = (path) => plansByPath.value.get(path) || []

const isExpanded = (path) => expandedPaths.value.includes(path)

const toggleExpand = (path) => {
  expandedPaths.value = isExpanded(path)
    ? expandedPaths.value.filter((item) => item !== path)
    : [...expandedPaths.value, path]
}

const selectPlanFromDropdown = (planId) => {
  selectedPlanId.value = planId
  dropdownOpen.value = false
}

const expandSelectedPlanPath = () => {
  if (!selectedPlan.value) return
  const paths = []
  let current = ''
  const parts = [selectedPlan.value.brigade, selectedPlan.value.battalion, selectedPlan.value.station].filter(Boolean)
  for (const part of parts) {
    current = current ? `${current}\\${part}` : part
    paths.push(current)
  }
  expandedPaths.value = Array.from(new Set([...expandedPaths.value, ...paths]))
}

const handleClickOutside = (event) => {
  if (!dropdownOpen.value) return
  const root = dropdownRef.value
  if (root && !root.contains(event.target)) {
    dropdownOpen.value = false
  }
}

const triggerPortal = (event) => {
  const target = event?.currentTarget
  const rect = target?.getBoundingClientRect?.()
  portal.value = {
    active: true,
    x: rect ? rect.left + rect.width / 2 : window.innerWidth / 2,
    y: rect ? rect.top + rect.height / 2 : window.innerHeight / 2,
  }
}

const clearPortal = () => {
  portal.value.active = false
}

const openPage = (key, event) => {
  triggerPortal(event)
  window.setTimeout(() => {
    activeNavKey.value = key
    viewMode.value = 'page'
  }, 150)
  window.setTimeout(clearPortal, 520)
}

const updatePointer = (event) => {
  const rect = event.currentTarget?.getBoundingClientRect?.()
  if (!rect) return
  pointer.value = {
    x: ((event.clientX - rect.left) / rect.width) * 100,
    y: ((event.clientY - rect.top) / rect.height) * 100,
  }
}

const loadPlans = async () => {
  try {
    plans.value = await getPlans()
    statusMessage.value = plans.value.length ? '' : '预案列表为空，请检查后端同步状态。'
    if (!selectedPlanId.value && plans.value.length) {
      selectedPlanId.value = plans.value[0].id
    } else if (selectedPlanId.value && !plans.value.some((plan) => plan.id === selectedPlanId.value)) {
      selectedPlanId.value = plans.value[0]?.id || null
    }
  } catch (error) {
    statusMessage.value = error?.response?.data?.detail || error?.message || '预案列表加载失败。'
    plans.value = []
  }
}

const loadDocument = async (planId) => {
  if (!planId) return
  loading.value = true
  try {
    currentDocument.value = await getPlanDocument(planId)
    activeNavKey.value = 'basic'
    viewMode.value = 'home'
  } catch (error) {
    statusMessage.value = error?.response?.data?.detail || error?.message || '预案内容加载失败。'
    currentDocument.value = null
  } finally {
    loading.value = false
  }
}

const handleSync = async () => {
  syncing.value = true
  statusMessage.value = '正在同步预案目录，请稍候...'
  try {
    await syncPlans()
    await loadPlans()
    if (selectedPlanId.value) {
      await loadDocument(selectedPlanId.value)
    }
    statusMessage.value = plans.value.length ? '同步完成。' : '同步完成，但当前未读取到预案。'
  } catch (error) {
    statusMessage.value = error?.response?.data?.detail || error?.message || '同步失败，请检查后端日志。'
  } finally {
    syncing.value = false
  }
}

watch(selectedPlanId, (planId) => {
  if (planId) {
    loadDocument(planId)
  }
})

watch(selectedPlan, () => {
  expandSelectedPlanPath()
})

watch(
  plans,
  (items) => {
    if (items.length && !selectedPlanId.value) {
      selectedPlanId.value = items[0].id
    }
  },
  { deep: true }
)

watch(filteredPlans, (items) => {
  if (!items.length) return
  if (!items.some((plan) => plan.id === selectedPlanId.value)) {
    selectedPlanId.value = items[0].id
  }
})

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await loadPlans()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
