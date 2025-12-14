import { createApp } from 'vue'
import App from './App.vue'

import {
  create,
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider
} from 'naive-ui'

const naive = create({
  components: [
    NConfigProvider,
    NMessageProvider,
    NDialogProvider,
    NNotificationProvider
  ]
})

createApp(App)
  .use(naive)
  .mount('#app')
