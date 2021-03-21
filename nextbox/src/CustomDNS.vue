<template>
	<div class="custom_dns">
		<div class="section">
			<h2>Custom Dynamic DNS Configuration</h2>
			Using this configuration you can configure any dynamic DNS service, which is supported
			by DDClient. This is considered an expert function, only use it if you know what you 
			are doing.
		</div>
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. <br>
			<input v-model="update.domain" type="text" class="txt">
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
		
			<!-- Raw ddclient configuration -->
			<h2>DDClient configuration</h2>
			By directly configuring DDClient you may use any supported Dynamic DNS service.
			The documentation for DDClient can be found 
			<a class="bold" href="https://ddclient.net/usage.html">here</a><br>
			<textarea v-model="update.conf" class="txtmult" /><br>
			<button type="button" @click="activate()">
				<span class="icon icon-confirm" />
				Finalize Configuration
			</button>
		</div>
		<div v-else-if="config.dns_mode !== 'config_done'" class="section">
			There is an active DNS Configuration. To activate the custom dynamic DNS 
			configuration you have to disable your existing configuration first.
		</div>
		<div v-else class="section">
			<button type="button" @click="disable()">
				<span class="icon icon-confirm" />
				Disable Custom Dynamic DNS Configuration
			</button>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
import Actions from '@nextcloud/vue/dist/Components/Actions'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'


export default {
	name: 'CustomDNS',

	components: {
		AppContentDetails,
		Actions,
		ActionRadio,
		ActionButton,
		ActionInput,
	},

	data() {
		return {
			// generics
			loading: false,
			userMessage: {
				domain: [],
				config: [],
			},
			
			config: {
				dns_mode: 'off',
				conf: '',
				domain: '',
				email: '',
			},
			
			// variables
			update: {
				dns_mode: 'off',
				conf: '',
				domain: '',
				captcha_png: '',
				captcha_id: '',
				captcha: '',
				email: '',
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
			const url = '/apps/nextbox/forward/config'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.config = res.data.data
			this.update.dns_mode = this.config.dns_mode
			this.update.domain = this.config.domain
			this.update.conf = this.config.conf.join('\n')
			this.update.desec_token = this.config.desec_token
			this.update.email = this.config.email

			if (this.config.dns_mode === 'desec') {
				this.refresh_captcha()
			}
		},

		async enable_https() {
			const url = '/apps/nextbox/forward/https/enable'
			const res = await axios.post(generateUrl(url)) 
				.then((res) => {
					// unreachable, will never return with success as this leads to server restart
				}).catch((e) => {
					this.status.nextMode = 'reload'
					this.status.mode = 'wait'
					this.status.waitFor = 30
					this.config.https = 443
					this.status.https.content = 'Enabling HTTPS done - reload pending...'
					showMessage('Switching from HTTP to HTTPS done')
					showMessage('Reloading in 30 secs')
					this.status.waitCallback = function(myThis, secs) {
						myThis.status.https.extra = (secs <= 0) ? '' : `reload in ${secs} secs`
					}
				})
		},

		async disable_https() {
			const url = '/apps/nextbox/forward/https/disable'
			const res = await axios.post(generateUrl(url)) 
				.then((res) => {
					// unreachable, will never return with success as this leads to server restart
				}).catch((e) => {
					this.status.nextMode = 'reload'
					this.status.mode = 'wait'
					this.status.waitFor = 30
					this.config.https = false
					this.status.https.content = 'Disabling HTTPS done - reload pending...'
					showMessage('Switching from HTTPS to HTTP done')
					showMessage('Reloading in 30 secs')
					this.status.waitCallback = function(myThis, secs) {
						myThis.status.https.extra = (secs <= 0) ? '' : `reload in ${secs} secs`
					}
				})
		},

		async disable() {
			this.update_config({
				dns_mode: 'off',
				conf: '',
				domain: '',
			})
		},

		check_domain() {
			if (this.update.domain === null || !this.update.domain.includes('.')) {
				this.userMessage.domain = ['Please insert a valid Domain']
				return false
			}

			this.userMessage.domain = []
			return true
		},

		async update_dns_mode() {
			this.userMessage = {}
			this.update_config({ dns_mode: this.update.dns_mode })
		},

		async finalize_config() {
			if (!this.check_email()) {
				return false
			}

			this.update_config({ 
				conf: this.update.conf,
				domain: this.update.domain,
				email: this.update.email,
				dns_mode: 'config_done',
			})
			this.restart_ddclient()
		},

		async setup_ddclient_config(ipType, domain, pwd) {
			const updateip = (ipType === 'ipv6') ? 'update6.dedyn.io' : 'update.dedyn.io'
			const ddclientConfig = 'protocol=dyndns2\n'
				+ `use=web, web=https://check${ipType}.dedyn.io/\n`
				+ 'ssl=yes\n'
				+ `server=${updateip}\n`
				+ `login='${domain}'\n`
				+ `password='${pwd}'\n`
				+ `${domain}\n`
			
			this.update_config({ 
				conf: ddclientConfig,
			})
			await this.restart_ddclient()
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

.custom_dns {
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

</style>
