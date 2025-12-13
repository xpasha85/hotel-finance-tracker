<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { uploadReceipt } from "../api/receipts";
import {
  listExpenses,
  createExpense,
  updateExpense,
  deleteExpense,
  restoreExpense,
} from "../api/expenses";
import { listCategories } from "../api/categories";
import { setAdminMode } from "../api/client";

const expenses = ref([]);
const categories = ref([]);

const filters = ref({
  period: "today", // today | yesterday | month
  category_id: null,
  payment_source: null,
  include_deleted: false,
});

// форма
const form = ref({
  amountRub: "", // ввод в рублях (строка)
  category_id: null,
  payment_source: "CASH",
  comment: "",
});

// режим редактирования
const editingId = ref(null);
const uploading = ref({});

const activeCategories = computed(() =>
  categories.value.filter((c) => c.is_active !== false)
);

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

function rubToCents(rubStr) {
  const s = String(rubStr).trim().replace(",", ".");
  if (!s) return null;
  const n = Number(s);
  if (!Number.isFinite(n) || n <= 0) return null;
  return Math.round(n * 100);
}

function resetFormKeepDefaults() {
  form.value.amountRub = "";
  form.value.comment = "";
  // category_id и payment_source не трогаем (удобно)
}

async function loadCategories() {
  const res = await listCategories();
  categories.value = res.data;

  if (!form.value.category_id) {
    const first = activeCategories.value[0];
    if (first) form.value.category_id = first.id;
  }
}

async function loadExpenses() {
  const params = {
    ...periodToDates(),
    category_ids: filters.value.category_id
      ? [filters.value.category_id]
      : undefined,
    payment_source: filters.value.payment_source || undefined,
    include_deleted: filters.value.include_deleted || undefined,
  };
  const res = await listExpenses(params);
  expenses.value = res.data;
}

async function onUploadReceipt(expenseId, file) {
  if (!file) return;

  try {
    uploading.value[expenseId] = true;

    // upload чека у тебя сейчас admin-only
    setAdminMode(true);

    await uploadReceipt(expenseId, file);

    await loadExpenses();
  } catch (e) {
    alert("Ошибка загрузки чека");
    console.error(e);
  } finally {
    uploading.value[expenseId] = false;
  }
}


function catName(id) {
  return categories.value.find((c) => c.id === id)?.name || id;
}

function startEdit(e) {
  editingId.value = e.id;
  form.value.amountRub = (e.amount_cents / 100).toFixed(2);
  form.value.category_id = e.category_id;
  form.value.payment_source = e.payment_source;
  form.value.comment = e.comment || "";
}

function cancelEdit() {
  editingId.value = null;
  resetFormKeepDefaults();
}

async function submitForm() {
  const amount_cents = rubToCents(form.value.amountRub);
  if (!amount_cents) {
    alert("Введите сумму (например 1200 или 1200.50)");
    return;
  }
  if (!form.value.category_id) {
    alert("Выберите категорию");
    return;
  }

  const payload = {
    amount_cents,
    payment_source: form.value.payment_source,
    category_id: form.value.category_id,
    comment: form.value.comment || null,
  };

  if (!editingId.value) {
    await createExpense(payload);
  } else {
    await updateExpense(editingId.value, payload);
    editingId.value = null;
  }

  resetFormKeepDefaults();
  await loadExpenses();
}

async function onDelete(id) {
  await deleteExpense(id);
  await loadExpenses();
}

async function onRestore(id) {
  setAdminMode(true);
  await restoreExpense(id);
  await loadExpenses();
}

onMounted(async () => {
  await loadCategories();
  await loadExpenses();
});

watch(
  filters,
  async () => {
    setAdminMode(!!filters.value.include_deleted);
    await loadExpenses();
  },
  { deep: true }
);
</script>

<template>
  <h2>Операции</h2>

  <div style="border: 1px solid #ddd; padding: 12px; margin-bottom: 12px">
    <h3 style="margin: 0 0 8px 0">
      {{ editingId ? "Редактировать расход" : "Добавить расход" }}
    </h3>

    <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center">
      <input
        v-model="form.amountRub"
        placeholder="Сумма, руб (например 1200.50)"
        style="width: 220px"
      />

      <select v-model="form.category_id" style="width: 220px">
        <option v-for="c in activeCategories" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <select v-model="form.payment_source" style="width: 160px">
        <option value="CASH">Наличные</option>
        <option value="CARD">Карта</option>
        <option value="BANK">Р/С</option>
      </select>

      <input
        v-model="form.comment"
        placeholder="Комментарий (необязательно)"
        style="width: 320px"
      />

      <button @click="submitForm">
        {{ editingId ? "Сохранить" : "Создать" }}
      </button>

      <button v-if="editingId" @click="cancelEdit">Отмена</button>
    </div>
  </div>

  <div style="margin-bottom: 8px">
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

    <label style="margin-left: 8px">
      <input type="checkbox" v-model="filters.include_deleted" />
      Показать удалённые (admin)
    </label>
  </div>

  <table
    border="1"
    cellpadding="6"
    cellspacing="0"
    style="border-collapse: collapse; width: 100%"
  >
    <thead>
      <tr>
        <th style="width: 160px">Дата</th>
        <th style="width: 120px">Сумма</th>
        <th>Категория</th>
        <th style="width: 120px">Источник</th>
        <th style="width: 120px">Статус</th>
        <th style="width: 220px">Действия</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="e in expenses"
        :key="e.id"
        :style="{ opacity: e.is_deleted ? 0.5 : 1 }"
      >
        <td>{{ new Date(e.spent_at).toLocaleString() }}</td>
        <td>{{ (e.amount_cents / 100).toFixed(2) }}</td>
        <td>{{ catName(e.category_id) }}</td>
        <td>{{ e.payment_source }}</td>
        <td>{{ e.is_deleted ? "Удалено" : "ОК" }}</td>
        <td>
          <button v-if="!e.is_deleted" @click="startEdit(e)">Изменить</button>
          <button v-if="!e.is_deleted" @click="onDelete(e.id)">Удалить</button>
          <button v-else @click="onRestore(e.id)">Восстановить</button>

          <!-- загрузка чека -->
          <label
            v-if="!e.is_deleted"
            style="margin-left:6px; border:1px solid #ccc; padding:2px 6px; cursor:pointer;"
          >
            📎 Чек
            <input
              type="file"
              accept="image/*,.pdf"
              style="display:none"
              @change="(ev) => onUploadReceipt(e.id, ev.target.files?.[0])"
            />
          </label>

          <span v-if="uploading[e.id]" style="margin-left:6px;">⏳</span>

          <a
            v-if="e.receipt_path"
            :href="`http://localhost:8000/receipts/${e.receipt_path}`"
            target="_blank"
            style="margin-left:6px;"
          >
            Открыть чек
          </a>
        </td>
      </tr>

      <tr v-if="expenses.length === 0">
        <td colspan="6" style="text-align: center; padding: 16px">
          Пока нет расходов по выбранным фильтрам
        </td>
      </tr>
    </tbody>
  </table>
</template>
