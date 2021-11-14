<template>
	<div id="tls" v-if="!loading">
		<div class="section">
			<h2>HTTPS / TLS Status</h2>
			<div v-if="!dns_mode.endsWith('_done')" icon="icon-close">
				To activate TLS encryption for your NextBox, first finish a DNS Configuration.
			</div>
			<div v-else>
				<StatusBar v-if="domain" preset="resolve_ipv4" />
				<StatusBar v-if="domain" preset="reach_http_ipv4" />
				<StatusBar v-if="domain" preset="resolve_ipv6" />
				<StatusBar v-if="domain" preset="reach_http_ipv6" />
				
				<div v-if="https">
					<StatusBar 
						state='success' 
						icon='checkmark'
						:text="'HTTPS / TLS is activated, your Nextcloud is available via ' + toLink(domain)" />
				</div>
				<div v-else>
					<StatusBar state='warning' icon='error' text='HTTPS / TLS is not activated' />
				</div>
			</div>
		</div>

		<div v-if="status && status.ips" class="section">
			<h2>Network Information</h2>
			Using IPv4 address: <b>{{ status.ips.ipv4 }}</b><br />
			Using IPv6 address: <b>{{ status.ips.ipv6 || '(No IPv6 support)'}}</b>
		</div>

		<div v-if="dns_mode.endsWith('_done')" class="section">
			<h2>HTTPS / TLS Management</h2>
			Enabling or Disabling HTTPS might need a restart of your browser to properly
			access your Nextcloud afterwards, as caching sometimes leads to issues. <br>
			It might also be needed to clear your browser cache/cookies, once you enable or disable TLS.<br><br>
			<div v-if="https">
				<div>
					<h3>Certificate Information</h3>
					Registered domain: <b>{{ (cert ? cert.name : 'checking...') }}</b><br>
					Expiry date: <b>{{ (cert ? cert.expiryDate.toLocaleString() : 'checking...') }}</b><br>
					Valid for: <b>{{ (cert ? cert.validForDays + ' days' : 'checking...') }}</b><br>
				</div>
				<br>
				<button v-tooltip="ttDisable" 
					type="button" 
					:disabled="loadingButton" 
					@click="disable()">
					<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-close')" />
					Disable HTTPS
				</button>
			</div>
			<div v-else>
				Activate HTTPS / TLS for your configured domain: <b>"{{ domain }}"</b>:
				<div v-if="dns_mode !== 'desec_done'">
					Please provide a valid E-Mail,
					which will be used to acquire a Let's Encrypt Certificate.
					<input v-model="update.email" type="text" @change="validateEMail">
					<br><span v-if="userMessage.email" class="error-txt">{{ userMessage.email.join(" ") }}</span>
				</div><br>
				<button v-tooltip="ttEnable" 
					type="button" 
					:disabled="enableDisabled" 
					@click="enable()">
					<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
					Enable HTTPS 
				</button>
			</div>
			
			<StatusBar v-if="showTimer" :status="timerStatus" />
			
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

//import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
//import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
//import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
//import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'
//import Modal from '@nextcloud/vue/dist/Components/Modal'


import UtilsMixin from './UtilsMixin.js'
import StatusBar from './StatusBar'


export default {
	name: 'TLS',
	mixins: [UtilsMixin],

	components: {
		StatusBar,
	},

	data() {
		return {
			// generics
			loading: true,
			loadingButton: false,

			// config (refreshed)
			domain: '',
			email: '',
			cert: {},
			https: false,
			dns_mode: '',

			// status data
			status: null,

			// intervall stuff
			interval: null,
			intervalStartedAt: null,
			
			// update-ables
			update: {
				email: '',
			},

			// user messaging
			userMessage: {
				email: [],
			},

			// consts/texts
			ttEnable: 'This will use your e-mail address to register a certificate '
					+ 'at Let\'s Crypt and install it to your NextBox\' Nextcloud instance. '
					+ 'Afterwards your NextBox shall be available using HTTPS.',
			ttDisable: 'Disabling HTTPS will remove the currently used certificate.'
					 + 'Your NextBox will only be available without encryption using http',
		}
	},

	computed: {
		enableDisabled() {
			return this.loadingButton || !this.validateEMail()
		},

		timerStatus() {
			return {
				icon: 'loading-small',
				text: `<b>Please wait</b> - active job: <b>${this.status.tls.what} (${this.status.tls.state})</b>`,
				extra: ((new Date() - this.intervalStartedAt) / 1e3).toFixed() + 'secs',
				state: 'neutral',
			}
		},
		showTimer() {
			if (this.interval) {
				return true
			} else if (this.status && this.status.tls && this.status.tls.state === 'running') {
				return true
			}
			return false
		},
	},

	async mounted() {
		await this.refresh()
		this.loading = false
		this.status = await this.getStatus()
		if (this.status && this.status.tls && this.status.tls.state === 'running') {
			if (!this.interval) {
				this.interval = window.setInterval(this.getStatusUntilDone, 1000)
				this.intervalStartedAt = new Date()
			}
		}
	},

	async beforeDestroy() {
		if (this.interval) {
			window.clearInterval(this.interval)
			this.interval = null
		}
	},

	methods: {
		async refresh() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/https'))
				this.domain = res.data.data.domain
				this.email = res.data.data.email
				this.cert = res.data.data.cert
				this.https = res.data.data.https
				this.dns_mode = res.data.data.dns_mode
				this.update.email = (this.email) ? this.email : ''
			} catch (e) {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			}

			this.loadingButton = false

			// if domain is available check resolv/reachable
			if (this.domain && this.dns_mode.endsWith('_done')) {

				axios.get(generateUrl('/apps/nextbox/forward/certs')).then((res) => {
					this.cert = res.data.data.cert
					if (this.cert) {
						const toks = this.cert.expiry.split(' ')
						this.cert.expiryDate = new Date(toks[0] + ' ' + toks[1])
						this.cert.validForDays = toks[3]
					}
				}).catch((e) => {
					console.error(e)
					showError(t('nextbox', 'Connection Failed'))
				})
			}
		},

		async getStatusUntilDone() {
			this.status = await this.getStatus()

			if (this.status) {
				const state = this.status.tls.state
				if (state === 'fail') {
					window.clearInterval(this.interval)
					const reason = {
						acquire: 'could not acquire certificate',
						'apache-config': 'failed setting up apache config',
						'domain-or-email': 'domain and/or e-mail missing'
					}
					showError(`Failed setting up HTTPS/TLS, ${reason[this.status.tls.what]}`)
					this.loadingButton = false
					this.intervalStartedAt = null
					this.interval = null

				} else if (state === 'success') {
					window.clearInterval(this.interval)
					showMessage('Acquiring certificate done, waiting 15secs before reloading...')
					setTimeout(() => {
						window.location.replace(`https://${this.domain}`)
					}, 15000)
				}

			// assume the process completed and Apache is restarting
			} else {
				window.clearInterval(this.interval)
				showMessage('Acquiring certificate done, waiting 15secs before reloading...')
				setTimeout(() => {
					window.location.replace(`https://${this.domain}`)
				}, 15000)
			}
		},

		async enable() {
			this.loadingButton = true

			const url = '/apps/nextbox/forward/https/enable'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const data = qs.stringify({
				domain: this.domain,
				email: this.update.email,
			})

			this.intervalStartedAt = new Date()
			
			const res = await axios.post(generateUrl(url), data, options).then((res) => {
				this.interval = window.setInterval(this.getStatusUntilDone, 1000)
			
			}).catch((e) => {
				showError('Connection failed')
				console.error(e)
				this.loadingButton = false
			})
		},

		async disable() {
			this.loadingButton = true
		
			const url = '/apps/nextbox/forward/https/disable'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const data = qs.stringify({})

			const res = await axios.post(generateUrl(url), data, options).then((res) => {
				if (res.data.result === 'success') {
					// actually never reached code, just to be save 
					setTimeout(() => {
						window.location.replace(`http://${this.domain}`)
					}, 60000)
					showSuccess(res.data.msg)
				} else {
					showError(res.data.msg)
					this.loadingButton = false
				}

			}).catch((e) => {
				// expected behavior for success :/
				setTimeout(() => {
					this.loadingButton = false
					window.location.replace(`http://${this.domain}`)
				}, 60000)
				showSuccess('finished, reloading in 60secs...')
				//console.error(e)
			})
		},

		validateEMail() {
			if (this.update.email === '' || this.update.email.length < 4) {
				this.userMessage.email = [
					'Please enter an e-mail address',
				]
				return false
			}
			const pat = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
			if (!pat.test(this.update.email)) {
				this.userMessage.email = [
					'Please enter a valid e-mail address',
				]
				return false
			}
			this.userMessage.email = []
			return true
		},
	},
}
</script>


<style scoped>

#tls {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}


.modal-box {
	width: 50vw;
	text-align: center;
	padding: 5vh;
}


</style>
