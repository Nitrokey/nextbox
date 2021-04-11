<template>
	<div class="remote">
		<!-- Done View -->
		<div v-if="config.dns_mode !== 'off' || config.proxy_active" class="section">
			<h2>Remote Access - Status</h2>
			
			<div>
				<span v-if="config.domain" :class="'tag ' + status.resolve.state"><span :class="'tag-icon ' + status.resolve.icon" />
					<span class="tag-content">{{ status.resolve.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.resolve.extra }}</span>
				</span>
			</div>

			<div>
				<span v-if="config.domain" :class="'tag ' + status.http.state"><span :class="'tag-icon ' + status.http.icon" />
					<span class="tag-content">{{ status.http.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.http.extra }}</span>
				</span>
			</div>

			<div v-if="config.proxy_active">
				<span :class="'tag ' + status.proxy.state"><span :class="'tag-icon ' + status.proxy.icon" />
					<span class="tag-content">{{ status.proxy.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.proxy.extra }}</span>
				</span>
			</div>

			<div v-if="status.help">
				{{ status.help }}
			</div>
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
				</li>
				<li v-tooltip="ttConfig" class="remote-action" @click="$emit('newPage', 'remote_custom_dns')">
					<span class="remote-icon icon-settings" />
					Custom Dynamic DNS Configuration
				</li-->
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


export default {
	name: 'Remote',

	components: {
	},

	data() {
		return {
			// generics
			loading: false,

			config: {
				https_port: false,
				proxy_active: false,
				dns_mode: 'off',
				proxy_domain: '',
				domain: false,

			},

			// user messaging
			userMessage: {},
			
			status: {
				resolve: { state: 'neutral', icon: 'icon-loading-small', content: 'DNS resolve testing pending', extra: '' },
				http: { state: 'neutral', icon: 'icon-loading-small', content: 'Reachability waiting to be tested', extra: '' },
				proxy: { state: 'neutral', icon: 'icon-loading-small', content: 'Quickstart remote access test pending', extra: '' },
			},

			// variables
			update: {
			},
		}
	},

	computed: {
	},

	async mounted() {
		await this.refresh()
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

			// get ipv4 resolve
			axios.get(generateUrl('/apps/nextbox/forward/dyndns/test/resolve/ipv4')).then((res) => {
				if (res.data.result === 'success') {
					this.status.resolve = {
						state: 'success',
						icon: 'icon-checkmark',
						content: `Successfully resolved: ${this.config.domain} to: ${res.data.data.ip}`
					}
				} else {
					let suffix = ''
					if (res.data.data) {
						suffix = `need: ${res.data.data.ip} found: ${res.data.data.resolve_ip}`
					}
					this.status.resolve = {
						state: 'error',
						icon: 'icon-close',
						content: `Failed resolving: ${this.config.domain} ${suffix}`
					}
				}
			}).catch((e) => {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			})
			
			// get general (http) reachability
			axios.get(generateUrl('/apps/nextbox/forward/dyndns/test/http')).then((res) => {
				if (res.data.result === 'success') {
					this.status.http = {
						state: 'success',
						icon: 'icon-checkmark',
						content: `Successfully tested reachability for: ${this.config.domain}`
					}
				} else {
					this.status.http = {
						state: 'error',
						icon: 'icon-close',
						content: `Failed reachability for: ${this.config.domain}`
					}
				}
			}).catch((e) => {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			})

			// get proxy reachability
			axios.get(generateUrl('/apps/nextbox/forward/dyndns/test/proxy')).then((res) => {
				if (res.data.result === 'success') {
					this.status.proxy = {
						state: 'success',
						icon: 'icon-checkmark',
						content: `Successfully tested reachability for: ${this.config.proxy_domain}`
					}
				} else {
					this.status.proxy = {
						state: 'error',
						icon: 'icon-close',
						content: `Failed reachability for: ${this.config.proxy_domain}`
					}
				}
			}).catch((e) => {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			})
		},
	},
}
</script>


<style scoped>

.remote {
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
