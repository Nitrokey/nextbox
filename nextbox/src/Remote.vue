<template>
	<div id="remote" v-if="!loading">
		<!-- Done View -->
		<div v-if="config.dns_mode !== 'off' || config.proxy_active" class="section">
			<h2>Remote Access - Status</h2>
			
			<StatusBar v-if="config.domain" preset="resolve_ipv4" />
			<StatusBar v-if="config.domain" preset="resolve_ipv6" />
			<StatusBar v-if="config.domain" preset="reach_http_ipv4" />
			<StatusBar v-if="config.domain" preset="reach_http_ipv6" />
			<StatusBar v-if="config.proxy_active" preset="reach_proxy" />
				
		</div>
		<!-- no status view -->
		<div v-else class="section">
			<h2>Remote Access - Not Configured</h2>
			Your NextBox is not yet configured for remote access. Please select one of the possible configurations below.
			<ul>
				<li class="remote-action" @click="$emit('newPage', 'remote_proxy')">
					<span class="remote-icon icon-star" />
					Backwards Proxy Configuration (recommended)
				</li>
				<!--li v-tooltip="ttDesec" class="remote-action" @click="$emit('newPage', 'remote_dyndns')">
					<span class="remote-icon icon-comment" />
					Guided Dynamic DNS Configuration (DeSEC)
				</li-->
				<li v-tooltip="ttConfig" class="remote-action" @click="$emit('newPage', 'remote_custom_dns')">
					<span class="remote-icon icon-settings" />
					Custom Dynamic DNS Configuration
				</li>
				<li class="remote-action" @click="$emit('newPage', 'remote_static_dns')">
					<span class="remote-icon icon-public" />
					Static Domain Configuration
				</li>
			</ul>
		</div>
	</div>
</template>



<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
// import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
//import qs from 'qs'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
// import Actions from '@nextcloud/vue/dist/Components/Actions'
// import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
// import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
// import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'



import UtilsMixin from './UtilsMixin.js'
import StatusBar from './StatusBar'



export default {
	name: 'Remote',
	mixins: [UtilsMixin],

	components: {
		StatusBar,
	},

	data() {
		return {
			// generics
			loading: true,

			config: {
				https_port: false,
				proxy_active: false,
				dns_mode: 'off',
				proxy_domain: '',
				domain: false,

			},

			// user messaging
			userMessage: {},
			
			// variables
			update: {
			},
		}
	},

	computed: {
	},

	async mounted() {
		await this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/config'))
				this.config = res.data.data
			} catch (e) {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			}
		},
	},
}
</script>


<style scoped>

#remote {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

.remote-action {
	margin-top: 10px;
	font-size: 1.1em;
	font-weight: bold;
	vertical-align: middle;
	line-height: 48px;
	cursor: pointer;
	width: fit-content;
}

.remote-icon {
	cursor: inherit;
	opacity: 1;
	background-position-y: -1px;
	margin-right: 8px;
	margin-left: 4px;
	background-repeat: no-repeat;
	display: inline-block;
	vertical-align: middle !important;
}

.remote-icon:hover {
	opacity: 0.7;
}

</style>
