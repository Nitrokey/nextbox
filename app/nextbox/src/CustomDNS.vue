<template>
	<div id="custom_dns" v-if="!loading">
		<div class="section">
			<h2>Custom Dynamic DNS Configuration</h2>
			Using this configuration you can configure any dynamic DNS service, which is supported
			by DDClient. This is considered an expert function, only use it if you know what you 
			are doing.
		</div>
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. <br>
			<input v-model="update.domain" 
				type="text" 
				class="txt" 
				@change="checkDomain()">
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
		
			<!-- Raw ddclient configuration -->
			<h2>DDClient configuration</h2>
			By directly configuring DDClient you are free to use any supported dynamic DNS service.
			The <span v-html="toLink('ddclient.net/#configuration', 'documentation')" /> for DDClient contains lots 
			of examples and <span v-html="toLink('ddclient.net/usage.net', 'usage scenarios')" />.<br>
			<textarea v-model="update.conf" 
				class="txtmult" 
				@change="checkConf()" />
			<br><span v-if="userMessage.conf" class="error-txt">{{ userMessage.conf.join(" ") }}</span><br>
			<button type="button" :disabled="activateDisabled" @click="activate()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Activate Configuration
			</button>
		</div>
		<div v-else-if="config.dns_mode !== 'config_done'" class="section">
			There is an active DNS Configuration. To activate the custom dynamic DNS 
			configuration you have to disable your existing configuration first.
		</div>
		<div v-else class="section">
			<StatusBar v-if="config.domain" preset="resolve_ipv4" />
			<StatusBar v-if="config.domain" preset="resolve_ipv6" /><br>
			This DNS configuration is active for the domain: <b>{{ update.domain }}</b><br><br>
			<button type="button" @click="$emit('newPage', 'tls')">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Continue to TLS activation
			</button>
			<button type="button" 
				class="right" 
				:disabled="config.https_port" 
				@click="disable()">

				<span class="icon icon-close" />
				Disable Configuration
			</button>

			<div v-if="config.https_port">
				<br>
				Disabling this configuration is not allowed with activated TLS.
			</div>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/style.css'
import { generateUrl } from '@nextcloud/router'
import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
// import Actions from '@nextcloud/vue/dist/Components/Actions'
// import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
// import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
// import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'


import UtilsMixin from './UtilsMixin.js'
import StatusBar from './StatusBar.vue'


export default {
	name: 'CustomDNS',
	mixins: [UtilsMixin],

	components: {
		StatusBar,
	},

	data() {
		return {
			// generics
			loading: true,
			loadingButton: false,

			// user messaging
			userMessage: {
				domain: [],
				conf: [],
			},
			
			config: {
				dns_mode: 'off',
				conf: '',
				domain: '',
				https_port: false,
			},
			
			// variables
			update: {
				dns_mode: 'off',
				conf: '',
				domain: '',
			},
		}
	},

	computed: {
		activateDisabled() {
			return this.loadingButton || !this.checkDomain() || !this.checkConf()
		},
	},

	async mounted() {
		await this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			const url = '/apps/nextbox/forward/config'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.config = res.data.data
			this.update.dns_mode = this.config.dns_mode
			this.update.domain = this.config.domain
			this.update.conf = this.config.conf
			this.update.https_port = this.config.https_port
		},

		checkDomain() {
			const pat = /^((?:(?:(?:\w[.\-+]?)*)\w)+)((?:(?:(?:\w[.\-+]?){0,62})\w)+)\.(\w{2,6})$/
			if (!pat.test(this.update.domain)) {
				this.userMessage.domain = ['Please insert a valid domain']
				return false
			}
			if (this.update.domain.includes('_')) {
				this.userMessage.domain = ['The domain may not contain underscores "_".']
				return false
			}
			this.userMessage.domain = []
			return true
		},

		checkConf() {
			if (this.update.conf.length < 3) {
				this.userMessage.conf = ['Please insert a ddclient configuration']
				return false
			}
			this.userMessage.conf = []
			return true
		},

		async activate() {
			if (this.checkDomain() && this.checkConf()) {
				this.loadingButton = true
				await this.update_config({ 
					domain: this.update.domain,
					conf: this.update.conf,
					dns_mode: 'config_done',
				})
				this.loadingButton = false
			}
		},

		async disable() {
			this.update_config({
				dns_mode: 'off',
			})
		},

		async restart_ddclient() {
			const url = '/apps/nextbox/forward/service/ddclient/restart'
			axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.result === 'success') {
						showSuccess('DDClient Service restarted')
					} else {
						showError('DDClient Service restart failed!')
					}
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
		},

		async update_config(update) {
			const url = '/apps/nextbox/forward/config'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const res = await axios.post(generateUrl(url), qs.stringify(update), options)
				.catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
			this.refresh()
		},

	},
}
</script>


<style scoped>

.dns_radio {
	width: fit-content;
	display: block !important;
}

#custom_dns {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

.restart-button {
	display: block !important;
}

.captcha-txt {
	width: 160px;
}

.txtmult {
	width: 25vw;
	height: 10em;
}

.icon-history {
	min-height: 24px !important;
	min-width: 24px !important;
	background-size: 24px !important;
	vertical-align: unset !important;
}


.right {
	float: right;
	margin-right: 10%;
}


</style>
