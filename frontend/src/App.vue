<template>
  <div style="padding:16px">
    <h1>Hotel Finance Tracker</h1>
    <p>Frontend (Vue 3) работает.</p>
    <p>API health: <b>{{ health }}</b></p>
    <button @click="check">Check</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const health = ref("—");

async function check() {
  const r = await fetch("http://localhost:8000/health");
  const j = await r.json();
  health.value = j.ok ? "OK" : "NOT OK";
}
</script>
