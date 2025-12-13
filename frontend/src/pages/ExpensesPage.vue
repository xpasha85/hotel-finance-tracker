<script setup>
import { ref, onMounted, watch } from "vue";
import { listExpenses } from "../api/expenses";
import { listCategories } from "../api/categories";
import { setAdminMode } from "../api/client";

const expenses = ref([]);
const categories = ref([]);

const filters = ref({
  period: "today",   // today | yesterday | month
  category_id: null,
  payment_source: null,
  include_deleted: false,
});

function periodToDates() {
  const now = new Date();
  if (filters.value.period === "today") {
    return { date_from: now.toISOString().slice(0, 10) };
  }
  if (filters.value.period === "yesterday") {
    const d = new Date(now);
    d.setDate(d.getDate() - 1);
    const s = d.toISOString().slice(0, 10);
    return { date_from: s, date_to: s };
  }
  if (filters.value.period === "month") {
    const from = new Date(now.getFullYear(), now.getMonth(), 1);
    return { date_from: from.toISOString().slice(0, 10) };
  }
  return {};
}

async function loadExpenses() {
  const params = {
    ...periodToDates(),
    category_ids: filters.value.category_id ? [filters.value.category_id] : undefined,
    payment_source: filters.value.payment_source || undefined,
    include_deleted: filters.value.include_deleted || undefined,
  };
  const res = await listExpenses(params);
  expenses.value = res.data;
}

onMounted(async () => {
  categories.value = (await listCategories()).data;
  await loadExpenses();
});

watch(filters, loadExpenses, { deep: true });
</script>

<template>
  <h2>Операции</h2>

  <div>
    <select v-model="filters.period">
      <option value="today">Сегодня</option>
      <option value="yesterday">Вчера</option>
      <option value="month">Месяц</option>
    </select>

    <select v-model="filters.category_id">
      <option :value="null">Все категории</option>
      <option v-for="c in categories" :key="c.id" :value="c.id">
        {{ c.name }}
      </option>
    </select>

    <select v-model="filters.payment_source">
      <option :value="null">Все источники</option>
      <option value="CASH">Наличные</option>
      <option value="CARD">Карта</option>
      <option value="BANK">Р/С</option>
    </select>

    <label>
      <input type="checkbox" v-model="filters.include_deleted" @change="setAdminMode(filters.include_deleted)" />
      Показать удалённые (admin)
    </label>
  </div>

  <table border="1" cellpadding="4">
    <thead>
      <tr>
        <th>Дата</th>
        <th>Сумма</th>
        <th>Категория</th>
        <th>Источник</th>
        <th>Статус</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="e in expenses" :key="e.id" :style="{ opacity: e.is_deleted ? 0.5 : 1 }">
        <td>{{ new Date(e.spent_at).toLocaleDateString() }}</td>
        <td>{{ (e.amount_cents / 100).toFixed(2) }}</td>
        <td>{{ categories.find(c => c.id === e.category_id)?.name }}</td>
        <td>{{ e.payment_source }}</td>
        <td>{{ e.is_deleted ? "Удалено" : "ОК" }}</td>
      </tr>
    </tbody>
  </table>
</template>
