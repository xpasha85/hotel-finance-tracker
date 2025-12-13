<template>
  <div style="padding:16px; max-width: 980px; margin: 0 auto;">
    <h1>Шурале — Финансовый трекер</h1>
    <h2 style="margin-top: 8px;">Категории расходов</h2>

    <div style="display:flex; gap:12px; align-items:center; margin: 12px 0;">
      <label style="display:flex; gap:8px; align-items:center;">
        <input type="checkbox" v-model="showArchived" />
        Показать архивные
      </label>

      <button @click="load" :disabled="loading">
        {{ loading ? "Загрузка..." : "Обновить" }}
      </button>
    </div>

    <hr />

    <h3 style="margin-top:16px;">Добавить категорию</h3>
    <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
      <input v-model="newName" placeholder="Название" style="padding:8px; min-width: 260px;" />

      <select v-model="newParentId" style="padding:8px;">
        <option :value="''">Без родителя</option>
        <option v-for="p in parentOptions" :key="p.id" :value="p.id">
          {{ p.name }}
        </option>
      </select>

      <button @click="create" :disabled="!newName || loading">Создать</button>
    </div>

    <p v-if="error" style="color:#b00020; margin-top:10px; white-space:pre-wrap;">{{ error }}</p>

    <h3 style="margin-top:20px;">Список</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="width:45%;">Название</th>
          <th>Родитель</th>
          <th>Статус</th>
          <th style="width:240px;">Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in rows" :key="c.id" :style="c.is_active ? '' : 'background:#ffecec'">
          <td>
            <div style="display:flex; gap:8px; align-items:center;">
              <input v-model="editName[c.id]" style="padding:6px; width: 100%;" />
              <button @click="rename(c)" :disabled="loading || !editName[c.id]">Сохранить</button>
            </div>
          </td>
          <td>{{ parentName(c.parent_id) }}</td>
          <td>{{ c.is_active ? "Активна" : "В архиве" }}</td>
          <td>
            <button v-if="c.is_active" @click="archive(c)" :disabled="loading">Архивировать</button>
            <button v-else @click="restore(c)" :disabled="loading">Вернуть</button>
          </td>
        </tr>
      </tbody>
    </table>

    <p style="margin-top:12px; color:#666;">
      Временная защита на админ-действия: заголовок <code>X-Role: ADMIN</code>.
      Позже заменим на JWT.
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

type Category = {
  id: string;
  name: string;
  parent_id: string | null;
  is_active: boolean;
};

const loading = ref(false);
const error = ref<string | null>(null);
const showArchived = ref(false);

const data = ref<Category[]>([]);
const editName = ref<Record<string, string>>({});

const newName = ref("");
const newParentId = ref("");

const rows = computed(() => data.value);

const parentOptions = computed(() => {
  // Для выбора родителя берём только активные категории
  return data.value.filter((c) => c.is_active);
});

function parentName(parentId: string | null) {
  if (!parentId) return "—";
  const p = data.value.find((x) => x.id === parentId);
  return p ? p.name : "(не найден)";
}

async function api(path: string, init?: RequestInit) {
  const res = await fetch(`http://localhost:8000${path}`, init);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }
  // у нас везде json
  return res.json();
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const activeOnly = !showArchived.value;
    const list = await api(`/categories?active_only=${activeOnly ? "true" : "false"}`);
    data.value = list;
    editName.value = Object.fromEntries(list.map((c: Category) => [c.id, c.name]));
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function create() {
  loading.value = true;
  error.value = null;
  try {
    await api("/categories", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Role": "ADMIN",
      },
      body: JSON.stringify({
        name: newName.value.trim(),
        parent_id: newParentId.value ? newParentId.value : null,
      }),
    });
    newName.value = "";
    newParentId.value = "";
    await load();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function rename(c: Category) {
  loading.value = true;
  error.value = null;
  try {
    await api(`/categories/${c.id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-Role": "ADMIN",
      },
      body: JSON.stringify({ name: (editName.value[c.id] ?? "").trim() }),
    });
    await load();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function archive(c: Category) {
  loading.value = true;
  error.value = null;
  try {
    await api(`/categories/${c.id}/archive`, {
      method: "POST",
      headers: { "X-Role": "ADMIN" },
    });
    await load();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

async function restore(c: Category) {
  loading.value = true;
  error.value = null;
  try {
    await api(`/categories/${c.id}/restore`, {
      method: "POST",
      headers: { "X-Role": "ADMIN" },
    });
    await load();
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
