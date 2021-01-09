/**
 * @copyright Copyright (c) Nitrokey GmbH
 *
 * @author Markus Meissner <meissner@nitrokey.com>
 *
 * @license GNU AGPL version 3 or any later version
 */

import Vue from 'vue'
import App from './App'

//import { VTooltip } from '@nextcloud/vue'
import VTooltip from '@nextcloud/vue/dist/Directives/Tooltip'

Vue.directive('Tooltip', VTooltip)

/*import VTooltip from 'v-tooltip'
Vue.use(VTooltip, {
	//defaultHtml: false,
})*/



Vue.mixin({ methods: { t, n } })

export default new Vue({
	el: '#content',
	render: h => h(App),
})
