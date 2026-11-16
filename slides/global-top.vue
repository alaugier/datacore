<script setup lang="ts">
import { computed } from 'vue'
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
const progress = computed(() => `${(currentPage.value / total.value) * 100}%`)
</script>

<template>
  <div v-if="currentPage > 1" class="absolute left-0 right-0 top-0 h-1 bg-gray-400/10">
    <div
      class="h-full"
      style="background: linear-gradient(90deg, #1c7ed6, #22b8cf); transition: width 0.2s ease;"
      :style="{ width: progress }"
    />
  </div>
</template>
