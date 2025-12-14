<template>
  <div class="page">
    <div class="topbar">
      <div class="left">
        <n-h2 style="margin: 0">Операции</n-h2>
        <n-space align="center" size="small" style="margin-top: 6px">
          <n-button-group>
            <n-button size="small" :type="periodPreset === 'today' ? 'primary' : 'default'" @click="setPreset('today')">
              Сегодня
            </n-button>
            <n-button size="small" :type="periodPreset === 'yesterday' ? 'primary' : 'default'" @click="setPreset('yesterday')">
              Вчера
            </n-button>
            <n-button size="small" :type="periodPreset === '7d' ? 'primary' : 'default'" @click="setPreset('7d')">
              7 дней
            </n-button>
            <n-button size="small" :type="periodPreset === 'month' ? 'primary' : 'default'" @click="setPreset('month')">
              Месяц
            </n-button>
          </n-button-group>

          <n-date-picker
            v-model:value="rangeValue"
            type="daterange"
            size="small"
            clearable
            :shortcuts="dateShortcuts"
            @update:value="onRangeChanged"
          />
        </n-space>
      </div>

      <div class="right">
        <n-space align="center">
          <n-select
            v-model:value="filters.categoryIds"
            multiple
            clearable
            size="small"
            placeholder="Категории"
            :options="categoryOptions"
            style="min-width: 220px"
          />
          <n-select
            v-model:value="filters.paymentSource"
            clearable
            size="small"
            placeholder="Источник"
            :options="paymentSourceOptions"
            style="width: 140px"
          />

          <n-divider vertical />

          <n-space align="center" size="small">
            <n-text depth="3">Role:</n-text>
            <n-radio-group
              size="small"
              v-model:value="role"
              @update:value="onRoleChanged"
            >
              <n-radio-button value="MANAGER">Manager</n-radio-button>
              <n-radio-button value="ADMIN">Admin</n-radio-button>
            </n-radio-group>
          </n-space>

          <n-switch
            v-if="isAdmin"
            v-model:value="filters.includeDeleted"
            size="small"
            @update:value="reload"
          >
            <template #checked>Удалённые</template>
            <template #unchecked>Удалённые</template>
          </n-switch>

          <n-button type="primary" @click="openCreate">
            + Трата
          </n-button>
        </n-space>
      </div>
    </div>

    <n-card size="small" style="margin-top: 12px">
      <n-space justify="space-between" align="center">
        <n-space align="center" size="large">
          <div class="metric">
            <div class="metric__label">Итого</div>
            <div class="metric__value">{{ formatRub(totalRub) }}</div>
          </div>
          <div class="metric">
            <div class="metric__label">Кол-во</div>
            <div class="metric__value">{{ expenses.length }}</div>
          </div>
          <div class="metric">
            <div class="metric__label">Средний чек</div>
            <div class="metric__value">{{ formatRub(avgRub) }}</div>
          </div>
          <div class="metric">
            <div class="metric__label">Макс</div>
            <div class="metric__value">{{ formatRub(maxRub) }}</div>
          </div>
        </n-space>

        <n-button size="small" secondary @click="reload" :loading="loading">
          Обновить
        </n-button>
      </n-space>
    </n-card>

    <n-card size="small" style="margin-top: 12px" :content-style="{ padding: '0' }">
      <n-data-table
        :columns="columns"
        :data="expenses"
        :loading="loading"
        :row-key="rowKey"
        :pagination="false"
        @row-click="onRowClick"
        class="table"
      />
      <div v-if="!loading && expenses.length === 0" class="empty">
        <n-empty description="Нет расходов по выбранным фильтрам" />
      </div>
    </n-card>

    <!-- Drawer create/edit -->
    <n-drawer v-model:show="drawer.show" :width="460" placement="right">
      <n-drawer-content :title="drawer.mode === 'create' ? 'Добавить трату' : 'Редактировать трату'">
        <n-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-placement="top"
          require-mark-placement="right-hanging"
        >
          <n-form-item label="Сумма (₽)" path="amountRub">
            <n-input-number
              v-model:value="form.amountRub"
              :min="0"
              :step="50"
              style="width: 100%"
              placeholder="Например 1200.50"
            />
          </n-form-item>

          <n-form-item label="Категория" path="category_id">
            <n-select
              v-model:value="form.category_id"
              :options="activeCategoryOptions"
              placeholder="Выбери категорию"
            />
          </n-form-item>

          <n-form-item label="Источник оплаты" path="payment_source">
            <n-select
              v-model:value="form.payment_source"
              :options="paymentSourceOptions"
              placeholder="CASH / CARD / BANK"
            />
          </n-form-item>

          <n-form-item label="Дата/время (опционально)" path="spent_at">
            <n-date-picker v-model:value="form.spent_at" type="datetime" clearable />
          </n-form-item>

          <n-form-item label="Комментарий" path="comment">
            <n-input v-model:value="form.comment" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" />
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="space-between" align="center">
            <n-space>
              <n-button secondary @click="drawer.show = false">Закрыть</n-button>
            </n-space>

            <n-space>
              <n-button
                v-if="drawer.mode === 'edit'"
                type="error"
                secondary
                @click="onDelete"
              >
                Удалить
              </n-button>

              <n-button type="primary" :loading="saving" @click="onSave">
                {{ drawer.mode === 'create' ? 'Создать' : 'Сохранить' }}
              </n-button>
            </n-space>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, h } from 'vue'
import { useDialog, useMessage, NTag } from 'naive-ui'

// API (твои файлы)
import { listCategories } from '../api/categories.js'
import {
  listExpenses,
  createExpense,
  updateExpense,
  deleteExpense,
  restoreExpense
} from '../api/expenses.js'

import { setAdminMode } from '../api/client.js'

// -------------------- state --------------------
const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const saving = ref(false)

const categories = ref<any[]>([])
const expenses = ref<any[]>([])


const role = ref<'MANAGER' | 'ADMIN'>('MANAGER')
const isAdmin = computed(() => role.value === 'ADMIN')

// filters
const filters = reactive({
  dateFrom: '', // YYYY-MM-DD
  dateTo: '',   // YYYY-MM-DD
  categoryIds: [] as string[],
  paymentSource: null as null | 'CASH' | 'CARD' | 'BANK',
  includeDeleted: false
})

// date preset + range picker (Naive uses timestamp numbers)
const periodPreset = ref<'today' | 'yesterday' | '7d' | 'month' | 'custom'>('7d')
const rangeValue = ref<[number, number] | null>(null)

// -------------------- helpers --------------------
function pad2(n: number) {
  return String(n).padStart(2, '0')
}
function toYMD(d: Date) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}
function startOfDay(d: Date) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}
function endOfDay(d: Date) {
  const x = new Date(d)
  x.setHours(23, 59, 59, 999)
  return x
}
function setPreset(p: typeof periodPreset.value) {
  periodPreset.value = p
  const now = new Date()
  let from: Date
  let to: Date

  if (p === 'today') {
    from = startOfDay(now)
    to = endOfDay(now)
  } else if (p === 'yesterday') {
    const y = new Date(now)
    y.setDate(y.getDate() - 1)
    from = startOfDay(y)
    to = endOfDay(y)
  } else if (p === '7d') {
    const f = new Date(now)
    f.setDate(f.getDate() - 6)
    from = startOfDay(f)
    to = endOfDay(now)
  } else if (p === 'month') {
    const f = new Date(now.getFullYear(), now.getMonth(), 1)
    from = startOfDay(f)
    to = endOfDay(now)
  } else {
    // custom - не трогаем
    return
  }

  filters.dateFrom = toYMD(from)
  filters.dateTo = toYMD(to)
  rangeValue.value = [from.getTime(), to.getTime()]
  reload()
}

const dateShortcuts = {
  'Сегодня': () => {
    const n = new Date()
    return [startOfDay(n).getTime(), endOfDay(n).getTime()]
  },
  'Вчера': () => {
    const n = new Date()
    n.setDate(n.getDate() - 1)
    return [startOfDay(n).getTime(), endOfDay(n).getTime()]
  },
  '7 дней': () => {
    const n = new Date()
    const f = new Date()
    f.setDate(f.getDate() - 6)
    return [startOfDay(f).getTime(), endOfDay(n).getTime()]
  },
  'Месяц': () => {
    const n = new Date()
    const f = new Date(n.getFullYear(), n.getMonth(), 1)
    return [startOfDay(f).getTime(), endOfDay(n).getTime()]
  }
} as const

function onRangeChanged(v: [number, number] | null) {
  if (!v) {
    // если очистили — вернём 7d
    setPreset('7d')
    return
  }
  periodPreset.value = 'custom'
  const from = new Date(v[0])
  const to = new Date(v[1])
  filters.dateFrom = toYMD(from)
  filters.dateTo = toYMD(to)
  reload()
}

// -------------------- load --------------------
async function loadCategories() {
  const res = await listCategories()
  categories.value = res.data
}


async function reload() {
  loading.value = true
  try {
    const params: any = {
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      payment_source: filters.paymentSource || undefined
    }

    if (filters.categoryIds.length) {
      params.category_ids = filters.categoryIds
    }

    if (isAdmin.value) {
      params.include_deleted = filters.includeDeleted ? 'true' : 'false'
    }

    const res = await listExpenses(params)
    expenses.value = Array.isArray(res.data) ? res.data : []
  } catch (e: any) {
    message.error(e?.message || 'Ошибка загрузки расходов')
  } finally {
    loading.value = false
  }
}


function onRoleChanged(v: 'MANAGER' | 'ADMIN') {
  role.value = v
  setAdminMode(v === 'ADMIN')
  if (!isAdmin.value) {
    filters.includeDeleted = false
  }
  reload()
}

// -------------------- computed: metrics --------------------
function centsToRub(cents: number) {
  return (cents || 0) / 100
}
const totalRub = computed(() => expenses.value.reduce((sum, x) => sum + centsToRub(x.amount_cents), 0))
const avgRub = computed(() => (expenses.value.length ? totalRub.value / expenses.value.length : 0))
const maxRub = computed(() => {
  if (!expenses.value.length) return 0
  return Math.max(...expenses.value.map((x) => centsToRub(x.amount_cents)))
})

function formatRub(v: number) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(v || 0)
}

// categories map/options
const categoryMap = computed(() => {
  const m = new Map<string, any>()
  for (const c of categories.value) m.set(c.id, c)
  return m
})
const categoryOptions = computed(() =>
  categories.value.map((c) => ({ label: c.is_active ? c.name : `${c.name} (архив)`, value: c.id }))
)
const activeCategoryOptions = computed(() =>
  categories.value.filter((c) => c.is_active).map((c) => ({ label: c.name, value: c.id }))
)

const paymentSourceOptions = [
  { label: 'Наличные', value: 'CASH' },
  { label: 'Карта', value: 'CARD' },
  { label: 'Банк', value: 'BANK' }
] as const

// -------------------- table --------------------
const rowKey = (row: any) => row.id

function fmtDate(iso: string) {
  if (!iso) return ''
  // очень простой формат, без dayjs
  const d = new Date(iso)
  return `${pad2(d.getDate())}.${pad2(d.getMonth() + 1)} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`
}

const columns = computed(() => {
  const cols: any[] = [
    {
      title: 'Дата',
      key: 'spent_at',
      width: 120,
      render(row: any) {
        return fmtDate(row.spent_at)
      }
    },
    {
      title: 'Сумма',
      key: 'amount_cents',
      width: 130,
      render(row: any) {
        return formatRub(centsToRub(row.amount_cents))
      }
    },
    {
      title: 'Категория',
      key: 'category_id',
      render(row: any) {
        const c = categoryMap.value.get(row.category_id)
        return c ? c.name : row.category_id
      }
    },
    {
      title: 'Источник',
      key: 'payment_source',
      width: 120,
      render(row: any) {
        const map: any = { CASH: 'Наличные', CARD: 'Карта', BANK: 'Банк' }
        return h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => map[row.payment_source] || row.payment_source })
      }
    },
    {
      title: 'Статус',
      key: 'is_deleted',
      width: 110,
      render(row: any) {
        return row.is_deleted
          ? h(NTag, { size: 'small', type: 'error', bordered: false }, { default: () => 'Удалено' })
          : h(NTag, { size: 'small', type: 'success', bordered: false }, { default: () => 'Ок' })
      }
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 160,
      render(row: any) {
        return h(
          'div',
          { style: 'display:flex; gap:8px; align-items:center;' },
          [
            h(
              'a',
              {
                href: '#',
                onClick: (e: any) => {
                  e.preventDefault()
                  openEdit(row)
                }
              },
              'Редакт.'
            ),
            row.is_deleted && isAdmin.value
              ? h(
                  'a',
                  {
                    href: '#',
                    onClick: (e: any) => {
                      e.preventDefault()
                      onRestore(row)
                    }
                  },
                  'Восст.'
                )
              : null
          ].filter(Boolean)
        )
      }
    }
  ]
  return cols
})

function onRowClick(row: any) {
  openEdit(row)
}

// -------------------- drawer form --------------------
const drawer = reactive({
  show: false,
  mode: 'create' as 'create' | 'edit',
  editingId: null as string | null
})

const formRef = ref()
const form = reactive({
  amountRub: null as number | null,
  payment_source: null as null | 'CASH' | 'CARD' | 'BANK',
  category_id: null as string | null,
  comment: '' as string,
  spent_at: null as number | null // timestamp ms for datetime picker
})

const rules = {
  amountRub: {
    required: true,
    message: 'Укажи сумму',
    trigger: ['input', 'blur'],
    validator: (_: any, v: any) => (typeof v === 'number' && v > 0 ? true : new Error('Сумма должна быть > 0'))
  },
  payment_source: { required: true, message: 'Выбери источник', trigger: ['change', 'blur'] },
  category_id: { required: true, message: 'Выбери категорию', trigger: ['change', 'blur'] }
}

function resetForm() {
  form.amountRub = null
  form.payment_source = null
  form.category_id = null
  form.comment = ''
  form.spent_at = null
}

function openCreate() {
  drawer.mode = 'create'
  drawer.editingId = null
  resetForm()
  drawer.show = true
}

function openEdit(row: any) {
  drawer.mode = 'edit'
  drawer.editingId = row.id
  form.amountRub = centsToRub(row.amount_cents)
  form.payment_source = row.payment_source
  form.category_id = row.category_id
  form.comment = row.comment || ''
  form.spent_at = row.spent_at ? new Date(row.spent_at).getTime() : null
  drawer.show = true
}

function rubToCents(rub: number) {
  return Math.round((rub || 0) * 100)
}

async function onSave() {
  saving.value = true
  try {
    await formRef.value?.validate()

    const payload: any = {
      amount_cents: rubToCents(form.amountRub || 0),
      payment_source: form.payment_source,
      category_id: form.category_id,
      comment: form.comment?.trim() || null,
      spent_at: form.spent_at ? new Date(form.spent_at).toISOString() : null
    }

    if (drawer.mode === 'create') {
      await createExpense(payload)
      message.success('Трата создана')
    } else {
      await updateExpense(drawer.editingId!, payload)
      message.success('Изменения сохранены')
    }

    drawer.show = false
    await reload()
  } catch (e: any) {
    if (e?.message) message.error(e.message)
    else message.error('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!drawer.editingId) return
  dialog.warning({
    title: 'Удалить трату?',
    content: 'Трата будет помечена как удалённая (soft-delete).',
    positiveText: 'Удалить',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await deleteExpense(drawer.editingId!)
        message.success('Удалено')
        drawer.show = false
        await reload()
      } catch (e: any) {
        message.error(e?.message || 'Ошибка удаления')
      }
    }
  })
}

async function onRestore(row: any) {
  dialog.info({
    title: 'Восстановить?',
    content: 'Трата станет снова активной.',
    positiveText: 'Восстановить',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await restoreExpense(row.id)
        message.success('Восстановлено')
        await reload()
      } catch (e: any) {
        message.error(e?.message || 'Ошибка восстановления')
      }
    }
  })
}

// -------------------- lifecycle --------------------
onMounted(async () => {
  // default role manager
  setAdminMode(false)

  await loadCategories()
  setPreset('7d')
})
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

@media (max-width: 1100px) {
  .topbar {
    flex-direction: column;
    align-items: stretch;
  }
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric__label {
  font-size: 12px;
  opacity: 0.7;
}
.metric__value {
  font-size: 18px;
  font-weight: 800;
}

.table :deep(.n-data-table-th) {
  font-weight: 700;
}

.empty {
  padding: 18px;
}
</style>
