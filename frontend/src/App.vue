<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-layout has-sider style="height: 100vh">
            <n-layout-sider
              bordered
              collapse-mode="width"
              :collapsed-width="64"
              :width="240"
              show-trigger
            >
              <div class="brand">
                <div class="brand__title">Шурале</div>
                <div class="brand__sub">Finance Tracker</div>
              </div>

              <n-menu
                :value="activeKey"
                :options="menuOptions"
                @update:value="onMenu"
              />
            </n-layout-sider>

            <n-layout>
              <n-layout-header bordered class="header">
                <div class="header__left">
                  <div class="header__title">Финансовый трекер</div>
                </div>

                <div class="header__right">
                  <n-tag size="small" type="info" :bordered="false">MVP</n-tag>
                </div>
              </n-layout-header>

              <n-layout-content class="content">
                <ExpensesPage />
              </n-layout-content>
            </n-layout>
          </n-layout>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { darkTheme, NIcon } from 'naive-ui'
import ExpensesPage from './pages/ExpensesPage.vue'
import { CashOutline, PricetagOutline } from '@vicons/ionicons5'

const activeKey = 'expenses'

const Icon = (icon: any) => () => h(NIcon, null, { default: () => h(icon) })

const menuOptions = [
  {
    label: 'Операции',
    key: 'expenses',
    icon: Icon(CashOutline)
  },
  {
    label: 'Категории',
    key: 'categories',
    disabled: true,
    icon: Icon(PricetagOutline)
  }
]

function onMenu(_key: string) {
  // пока без роутера
}
</script>

<style scoped>
.brand {
  padding: 14px 14px 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand__title {
  font-size: 16px;
  font-weight: 800;
  line-height: 1.2;
}
.brand__sub {
  font-size: 12px;
  opacity: 0.75;
  margin-top: 2px;
}

.header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header__title {
  font-weight: 800;
}

.content {
  padding: 16px;
  /* фон контента чуть отличается от layout — выглядит “дороже” */
  background: rgba(255, 255, 255, 0.02);
  min-height: calc(100vh - 56px);
}
</style>
