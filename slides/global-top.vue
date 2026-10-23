<script setup lang="ts">
import { useNav } from '@slidev/client'

const { currentPage } = useNav()
</script>

<template>
  <div
    v-if="currentPage > 1"
    class="absolute left-0 right-0 top-0 h-1"
    style="background: linear-gradient(90deg, #1c7ed6, #22b8cf, #1c7ed6); opacity: 0.6;"
  />
</template>
