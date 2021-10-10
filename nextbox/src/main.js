/**
 * @copyright Copyright (c) Nitrokey GmbH
 *
 * @author Markus Meissner <meissner@nitrokey.com>
 *
 * @license GNU AGPL version 3 or any later version
 */

import Vue from 'vue'
import App from './App'
import UtilsMixin from './UtilsMixin.js'

//import { VTooltip } from '@nextcloud/vue'
import VTooltip from '@nextcloud/vue/dist/Directives/Tooltip'

Vue.directive('Tooltip', VTooltip)


Vue.mixin(UtilsMixin)


Vue.mixin({ 
	methods: { t, n },

})

export default new Vue({
	el: '#content',
	render: h => h(App),
})







/*

// define an app that uses this mixin
const app = Vue.createApp({
	mixins: [myMixin]
  })
  
  app.mount('#mixins-basic') // => "hello from mixin!"*/