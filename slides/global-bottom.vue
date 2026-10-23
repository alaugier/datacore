<script setup lang="ts">
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()

// Plages de slides par bloc (à ajuster si le découpage change -- voir
// la numérotation réelle via `node list_slides.mjs` sur le serveur de
// dev avant de les modifier).
const BLOCKS = [
  { from: 6, to: 15, icon: '/icons/badge-bloc1.svg', label: 'Bloc 1 — Cadrage' },
  { from: 16, to: 24, icon: '/icons/badge-bloc2.svg', label: 'Bloc 2 — Collecte & Stockage' },
  { from: 25, to: 33, icon: '/icons/badge-bloc3.svg', label: 'Bloc 3 — Entrepôt OMEGA BI' },
  { from: 34, to: 40, icon: '/icons/badge-bloc4.svg', label: 'Bloc 4 — Data Lake OMEGA LAKE' },
]

const currentBlock = computed(() =>
  BLOCKS.find(b => currentPage.value >= b.from && currentPage.value <= b.to),
)
</script>

<template>
  <div v-if="currentPage > 1" class="abs-br m-4 flex items-center gap-2">
    <img v-if="currentBlock" :src="currentBlock.icon" :title="currentBlock.label" class="h-4 opacity-50">
    <span class="text-sm opacity-50 tabular-nums">{{ currentPage }} / {{ total }}</span>
  </div>
</template>
