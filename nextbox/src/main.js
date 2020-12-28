/**
 * @copyright Copyright (c) Nitrokey GmbH
 *
 * @author Markus Meissner <meissner@nitrokey.com>
 *
 * @license GNU AGPL version 3 or any later version
 */

import Vue from 'vue'
import App from './App'

Vue.mixin({ methods: { t, n } })

export default new Vue({
	el: '#content',
	render: h => h(App),
})
