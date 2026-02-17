/**
 * @copyright Copyright (c) Nitrokey GmbH
 *
 * @author Markus Meissner <meissner@nitrokey.com>
 *
 * @license GNU AGPL version 3 or any later version
 */

import { createApp } from 'vue'
import App from './App.vue'
import FloatingVue from 'floating-vue'
import 'floating-vue/dist/style.css'

const app = createApp(App)

// Setup floating-vue for tooltips
app.use(FloatingVue)

// Make translation functions available globally
app.config.globalProperties.t = t
app.config.globalProperties.n = n

app.mount('#content')






