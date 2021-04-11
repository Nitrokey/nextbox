<template>
	<div class="dyndns">
		<div class="section">
			<h2>Guided Dynamic DNS Configuration</h2>
			This wizard will guide you through the process of setting up remote access to your
			NextBox using the <a class="bold" href="http://desec.org">DeSEC</a> dynamic DNS service.<br>
			For a proper configuration you should know what kind of internet connection you are using 
			(IPv4, IPv6, DS-Lite) and how to configure port-forwarding on your internet router.
		</div>
		
		<!-- E-Mail Configuration -->
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>E-Mail Address</h2>
			Insert a valid E-Mail for the registrations to be used. You need access to this E-Mail 
			to complete Let's encrypt certificate acquisition, thus setting up TLS. 
			<span v-if="config.dns_mode === 'desec'">
				The guided registration process for the deSEC dynamic DNS service.
			</span>
			<br>
			<input v-model="update.email" type="text">
			<br><span v-if="userMessage.email" class="error-txt">
				{{ userMessage.email.join(" ") }}
			</span><br>
		
			<!-- Domain -->
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. The domain always has to end with <span class="bold">.dedyn.io</span>.<br>
			<input v-model="update.domain" type="text">
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
		
			<!-- Captcha deSEC & start registration... -->
			<h2>Captcha for DeSEC registration</h2>
			Plase solve this Captcha to verify for the dynamic DNS service (deSEC) that you are a human.<br>
			<img :src="update.captcha_png"><span class="icon icon-history" @click="refresh_captcha()" /><br>
			<input v-model="update.captcha" type="text" class="captcha-txt"><br>
			<span v-if="userMessageCaptcha" class="error-txt">
				{{ userMessageCaptcha }}
			</span><br>
			<button type="button" @click="register_desec(update)">
				<span class="icon icon-confirm" />
				Start registration ...
			</button><br>
		</div>

		<!-- deSEC token and finalize registration -->
		<div v-else-if="config.dns_mode === 'desec_2'" class="section">
			<h2>deSEC Activation Token</h2>
			<span class="bold">The registration using your provided E-Mail was successful</span>.<br>

			You should have received an E-Mail with an activation link. Please 
			click on this link and copy the presented token into this field:<br>

			<input v-model="update.desec_token" type="text"><br>
			<button type="button" @click="finalize_desec()">
				<span class="icon icon-confirm" />
				Finalize Configuration
			</button><br>
			<br>
			If you have not received an E-Mail this means you have already 
			been registered with this E-Mail at deSEC. If you know your password
			you can <a class="bold" href="https://desec.io/login">login here</a> and copy the 
			token from your account settings. During NextBox' automated process no 
			password is set, in order to acquire one you have to 
			<a class="bold" href="https://desec.io/reset-password">reset your password</a>.
		</div>
		<div v-else-if="config.dns_mode !== 'desec_done'" class="section">
			There is an active DNS Configuration. To activate the guided dynamic  
			DNS configuration you have to disable your existing configuration first.
		</div>
		<div v-else class="section">
			<button type="button" @click="disable()">
				<span class="icon icon-confirm" />
				Disable Guided Dynamic DNS Configuration
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
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
// import Actions from '@nextcloud/vue/dist/Components/Actions'
// import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
// import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
// import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'


export default {
	name: 'DynDNS',

	components: {
	},

	data() {
		return {
			// generics
			loading: false,
			userMessage: {},
			
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
		userMessageCaptcha() {
			if (this.userMessage.captcha) {
				const out = Object.keys(this.userMessage.captcha).map((key) => 
					this.userMessage.captcha[key].join(' ')).join('<br>')
				console.error(out)
				return out
			}
			return ''
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
			this.update.conf = this.config.conf.join('\n')
			this.update.desec_token = this.config.desec_token
			this.update.email = this.config.email

			if (this.config.dns_mode !== 'desec_2') {
				this.refresh_captcha()
			}
		},

		async refresh_captcha() {
			const captchaUrl = generateUrl('/apps/nextbox/forward/dyndns/captcha')
			const captchaRes = await axios.post(captchaUrl).catch((e) => {
				showError('Cannot aquire captcha from deSEC')
				console.error(e)
			})
			this.update.captcha_png = `data:image/png;base64,${captchaRes.data.data.challenge}`
			this.update.captcha_id = captchaRes.data.data.id
			this.update.captcha = ''
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

		check_email() {
			if (this.update.email === null || !this.update.email.includes('.') || !this.update.email.includes('@')) {
				this.userMessage.email = ['Please insert a valid E-Mail address']
				return false
			}
			if ('email' in this.userMessage) delete this.userMessage.email

			return true
		},

		check_domain() {
			if (this.update.domain === null || !this.update.domain.includes('.')) {
				this.userMessage.domain = ['Please insert a valid Domain']
				return false
			}
			if (!this.update.domain.endsWith('.dedyn.io')) {
				this.userMessage.domain = ['The Domain has to end with: <span class="bold">.dedyn.io</span>']
			}

			if ('domain' in this.userMessage) delete this.userMessage.domain

			return true
		},

		async update_dns_mode() {
			this.userMessage = {}
			this.update_config({ dns_mode: this.update.dns_mode })
		},

		async finalize_desec() {
			if (this.update.desec_token.length !== 28) {
				showError('The token is not valid')
				return
			}

			this.setup_ddclient_config(this.status.useIpType, this.config.domain, this.update.desec_token)

			this.update_config({ 
				desec_token: this.update.desec_token, 
				dns_mode: 'desec_done',
			})

			this.init_status()
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

		async register_desec(update) {
			if (!this.check_email() || !this.check_domain()) {
				this.refresh_captcha()
				return false
			}

			const url = '/apps/nextbox/forward/dyndns/register'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const res = await axios.post(generateUrl(url), qs.stringify(update), options)
				.catch((e) => {
					showError('Connection failed')
					console.error(e)
				})

			if (res.data.result !== 'success') {
				this.userMessage = res.data.data
				if (this.userMessage.detail) {
					showError(this.userMessage.detail)
				}
				showError(res.data.msg)
				this.refresh_captcha()
			} else {
				this.update_config({
					dns_mode: 'desec_2',
					domain: this.update.domain,
					email: this.update.email,
				})
			}
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

.dyndns {
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
