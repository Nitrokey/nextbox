<template>
	<div id="tls" v-if="!loading">
		<div class="section">
			<h2>HTTPS / TLS Configuration</h2>
			<div v-if="!dns_mode.endsWith('_done')" icon="icon-close">
				To activate TLS encryption for your NextBox, first finish a DNS Configuration.
			</div>
			<div v-else>
				<StatusBar v-if="domain" preset="resolve_ipv4" />
				<StatusBar v-if="domain" preset="resolve_ipv6" />
				<StatusBar v-if="domain" preset="reach_http_ipv4" />
				<StatusBar v-if="domain" preset="reach_http_ipv6" />
				
				<div v-if="https">
					<StatusBar 
						state='success' 
						icon='checkmark'
						:text="`HTTPS / TLS is activated, your Nextcloud is available via <a href='https://${domain}'>${domain}</a>`" />
			
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
					<StatusBar state='warning' icon='error' text='HTTPS / TLS is not activated' />
					<br>
					Activate HTTPS / TLS for your configured domain: <span class="bold">"{{ domain }}"</span>
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
				</div><br>
				Enabling or Disabling HTTPS might need a restart of your Browser to properly
				access your Nextcloud afterwards, as caching sometimes leads to issues. <br>
				It might also be needed to clear your browser cache/cookies, once you enable or disable TLS.
			</div>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

//import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
//import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
//import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
//import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'
//import Modal from '@nextcloud/vue/dist/Components/Modal'


import StatusBar from './StatusBar'


export default {
	name: 'TLS',
	
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
	},

	async mounted() {
		await this.refresh()
		this.loading = false
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
				}).catch((e) => {
					console.error(e)
					showError(t('nextbox', 'Connection Failed'))
				})
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

			const res = await axios.post(generateUrl(url), data, options).then((res) => {
				if (res.data.result === 'success') {
					setTimeout(() => {
						window.location.replace(`https://${this.domain}`)
					}, 5000)
					showSuccess(res.data.msg)
				} else {
					showError(res.data.msg)
					this.loadingButton = false
				}
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
					setTimeout(() => {
						window.location.replace(`http://${this.domain}`)
					}, 5000)
					showSuccess(res.data.msg)
				} else {
					showError(res.data.msg)
					this.loadingButton = false
				}
			}).catch((e) => {
				// expected behavior for success :/
				setTimeout(() => {
					window.location.replace(`http://${this.domain}`)
				}, 5000)
				showSuccess('redirecting in 5secs')
				console.error(e)
				this.loadingButton = false
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
