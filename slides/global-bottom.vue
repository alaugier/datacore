<script setup lang="ts">
import { useNav } from '@slidev/client'

const { currentPage, total } = useNav()
</script>

<template>
  <div v-if="currentPage > 1" class="abs-br m-4 text-sm opacity-50 tabular-nums">
    {{ currentPage }} / {{ total }}
  </div>
</template>
