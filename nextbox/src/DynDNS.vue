<template>
	<div id="dyndns" v-if="!loading">
		<div class="section">
			<h2>Guided Dynamic DNS Configuration</h2>
			This wizard will guide you through the process of setting up remote access to your
			NextBox using the {{ toLink('desec.org', 'deSEC') }} dynamic DNS service.<br>
			For a proper configuration you should know what kind of internet connection you are using 
			(IPv4, IPv6, Dual-Stack, DS-Lite) and how to access your internet router. Please find further 
			documentation at {{ docsLink }}.
		</div>
		
		
		<div v-if="config.dns_mode === 'off'" class="section">
			<!-- E-Mail Configuration -->
			<h2>Step One: E-Mail Address & Domain for DeSEC Registration</h2>
			Insert a valid E-Mail for the registration to be used. You need access to this E-Mail.
			<span v-if="config.dns_mode === 'desec'">
				The guided registration process for the deSEC dynamic DNS service.
			</span>
			<br>
			<input v-model="update.email" type="text">
			<br><span v-if="userMessage.email" class="error-txt">{{ userMessage.email.join(" ") }}</span><br>
		
			<!-- Domain -->
			Insert the designated full domain for your NextBox. The domain always has to end with <b>.dedyn.io</b>.<br>
			<input v-model="update.domain" type="text">
			<br><span v-if="userMessage.domain" class="error-txt" v-html="userMessage.domain.join(' ')" /><br>
		
			<button type="button" :disabled="activateRegister" @click="register_desec()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Register at deSEC
			</button>
			<button type="button" 
				class="right" 
				:disabled="activateRegister" 
				@click="next_step()">
				
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-play-next')" />
				Next (without register)
			</button>
			<br><span v-if="userMessage.global" class="error-txt" v-html="userMessage.global.join(' ')" /><br>
		</div>
		
		<div v-else-if="config.dns_mode === 'desec_2'" class="section">
			<!-- deSEC token -->
			<h2>Step Two: deSEC Activation Token</h2>
			<b>After completing registration with deSEC and verifing your E-Mail.</b><br>
			Please put in the token you have received from deSEC<br>

			<input v-model="update.desec_token" type="text">
			<br><span v-if="userMessage.desec_token" class="error-txt">{{ userMessage.desec_token.join(" ") }}</span><br>
		
			<button type="button" :disabled="activateDisabled" @click="finalize_desec()">
				<span class="icon icon-confirm" />
				Finalize Configuration
			</button>
			<button type="button" class="right" @click="last_step()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-play-previous')" />
				Back
			</button><br>
			<br>
			If you have not received an E-Mail this means you have already been
			registered with this E-Mail at deSEC. If you know your password you
			can {{ toLink('desec.io/login', 'login') }} and create a new token
			in your account settings. During NextBox' automated process no
			password is set, in order to acquire one you have to
			{{ toLink('desec.io/reset-password', 'reset your password') }} 
			before logging in.
		</div>
		
		<div v-else-if="config.dns_mode === 'desec_done'" class="section">
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

				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-close')" />
				Disable Configuration
			</button>
			<div v-if="config.https_port">
				<br>
				Disabling this configuration is not allowed with activated TLS.
			</div>
		</div>

		<div v-else class="section">
			There is an active DNS configuration.
			To activate the guided dynamic DNS configuration you have to disable your existing configuration first.
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


import { docsLink, toLink } from './utils.js'
import StatusBar from './StatusBar'


export default {
	name: 'DynDNS',


	components: {
		StatusBar,
	},

	data() {
		return {
			// generics
			loading: true,
			loadingButton: false,

			userMessage: {
				email: [],
				domain: [],
				desec_token: [],
				global: [],
			},
			
			config: {
				dns_mode: 'off',
				domain: '',
				email: '',
				desec_token: '',
				https_port: false,
			},
						
			// variables
			update: {
				dns_mode: 'off',
				domain: '',
				email: '',
				desec_token: ''
			},
		}
	},

	computed: {
		docsLink,

		activateRegister() {
			return this.loadingButton || !this.checkDomain() || !this.checkEMail()
		},
		activateDisabled() {
			return this.loadingButton || !this.checkDomain() || !this.checkEMail() || !this.checkToken()
		},
	},

	async mounted() {
		await this.refresh()
		this.loading = false
	},

	methods: {
		toLink,

		async refresh() {
			const url = '/apps/nextbox/forward/config'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.config = res.data.data
			this.update.dns_mode = this.config.dns_mode
			this.update.domain = this.config.domain || ''
			this.update.desec_token = this.config.desec_token || ''
			this.update.email = this.config.email || ''
		},

		checkEMail() {
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

		checkDomain() {
			const pat = /^((?:(?:(?:\w[.\-+]?)*)\w)+)((?:(?:(?:\w[.\-+]?){0,62})\w)+)\.(\w{2,6})$/
			if (!pat.test(this.update.domain)) {
				this.userMessage.domain = ['Please insert a valid domain']
				return false
			}
			if (!this.update.domain.endsWith('.dedyn.io')) {
				this.userMessage.domain = ['The domain has to end with: <b>.dedyn.io</b>']
				return false
			}
			const dotpat = new RegExp('\\.', 'g')
			if ((this.update.domain.match(dotpat) || []).length > 2) {
				this.userMessage.domain = ['The domain shall not contain multi-level subdomains. Bad: foo.bar.dedyn.io - Good: single.dedyn.io']
				return false
			}
			if (this.update.domain.includes('_')) {
				this.userMessage.domain = ['The domain may not contain underscores "_".']
				return false
			}

			this.userMessage.domain = []
			return true
		},

		checkToken() {
			const needlen = 28
			this.update.desec_token = this.update.desec_token.trim()
			const haslen = this.update.desec_token.length
			if (haslen !== needlen) {
				this.userMessage.desec_token = [`The token needs a length of exactly ${needlen} characters - currently: ${haslen}`]
				return false
			}
			this.userMessage.desec_token = []
			return true
		},

		async finalize_desec() {
			this.loadingButton = true
			if (!this.checkEMail() || !this.checkDomain() || !this.checkToken()) {
				return false
			}

			//this.setup_ddclient_config(this.config.domain, this.update.desec_token)

			this.update_config({ 
				desec_token: this.update.desec_token, 
				dns_mode: 'desec_done',
			})
			this.loadingButton = false
		},

		async last_step() {
			this.update_config({ 
				desec_token: this.update.desec_token, 
				dns_mode: 'off',
			})
			this.refresh()
		},

		async next_step() {
			this.update_config({ 
				dns_mode: 'desec_2',
				domain: this.update.domain,
				email: this.update.email,
			})
			this.refresh()
		},

		async disable() {
			this.update_config({
				dns_mode: 'off',
			})
			showMessage('Disabled config')
		},

		async register_desec() {
			this.loadingButton = true
			if (!this.checkEMail() || !this.checkDomain()) {
				return false
			}

			const url = '/apps/nextbox/forward/dyndns/register'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const res = await axios.post(generateUrl(url), qs.stringify(this.update), options)
				.catch((e) => {
					showError('Connection failed')
					console.error(e)
				})

			if (res.data.result !== 'success') {
				if (res.data.data) {
					if ('domain' in res.data.data) {
						this.userMessage.global = res.data.data.domain
					}
					if ('email' in res.data.data) {
						this.userMessage.global = res.data.data.email
					}
				}
				showError(res.data.msg)
			} else {
				this.update_config({
					domain: this.update.domain,
					email: this.update.email,
					dns_mode: 'desec_2',
				})
				showMessage('Success sending registration, check your emails...')
			}
			this.loadingButton = false
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

#dyndns {
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
