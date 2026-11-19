<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import mediumZoom from 'medium-zoom'

const props = defineProps<{
  src: string
  imgClass?: string
  imgStyle?: string
}>()

const el = ref<HTMLImageElement>()
let zoom: ReturnType<typeof mediumZoom> | null = null

onMounted(() => {
  if (!el.value)
    return
  zoom = mediumZoom(el.value, {
    margin: 24,
    background: 'rgba(255, 255, 255, 0.96)',
    scrollOffset: 0,
  })
})

onBeforeUnmount(() => {
  zoom?.detach()
  zoom = null
})
</script>

<template>
  <div class="zoomable-wrap">
    <img ref="el" :src="props.src" :class="props.imgClass" :style="props.imgStyle" class="zoomable-img">
    <div class="zoomable-hint">🔍 cliquer pour agrandir</div>
  </div>
</template>

<style scoped>
.zoomable-wrap {
  position: relative;
  display: inline-block;
}
.zoomable-img {
  cursor: zoom-in;
}
.zoomable-hint {
  position: absolute;
  bottom: 4px;
  right: 8px;
  font-size: 0.65rem;
  color: #868e96;
  opacity: 0;
  transition: opacity 0.15s ease;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 4px;
  padding: 1px 5px;
}
.zoomable-wrap:hover .zoomable-hint {
  opacity: 0.8;
}
</style>
