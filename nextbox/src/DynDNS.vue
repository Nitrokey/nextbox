<template>
	<div class="dyndns">
		<!-- MAIN MENU -->
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Choose a Dynamic DNS Configuration Mode</h2>
			To make your NextBox available outside of your internal network you need to configure
			a (dynamic) domain. Your Nextcloud instance will afterwards be available using this domain.
			<ActionRadio 
				v-tooltip.bottom="ttDesec" 
				name="dns_mode"
				value="desec" 
				class="dns_radio"
				@update:checked="update.dns_mode = 'desec'">
				Guided DynDNS Configuration (recommended)
			</ActionRadio>
			<ActionRadio  
				v-tooltip.bottom="ttStatic"
				value="static"
				class="dns_radio" 
				name="dns_mode" 
				@update:checked="update.dns_mode = 'static'">
				Static Domain
			</ActionRadio>
			<ActionRadio 
				v-tooltip.bottom="ttConfig" 
				name="dns_mode"
				value="config" 
				class="dns_radio" 
				@update:checked="update.dns_mode = 'config'">
				Raw DDClient Configuration
			</ActionRadio><br>
			<button type="button" @click="update_dns_mode()">
				<span class="icon icon-confirm" />
				Continue
			</button>
		</div>

		<!-- E-Mail Configuration -->
		<div v-if="['static', 'config', 'desec'].includes(config.dns_mode)" class="section">
			<h2>E-Mail Address</h2>
			Insert a valid E-Mail for the registrations to be used. You need access to this E-Mail 
			to complete Let's encrypt certificate acquisition, thus setting up TLS. 
			<span v-if="config.dns_mode === 'desec'">
				The guided registration process for the deSEC dynamic DNS service.
			</span>
			<br>
			<input v-model="update.email" type="text" class="txt">
			<br><span v-if="userMessage.email" class="error-txt">
				{{ userMessage.email.join(" ") }}
			</span><br>
			<!--button type="button" @click="update_email()">
				<span class="icon icon-confirm" />
				Save
			</button -->
		</div>

		<!-- Domain -->
		<div v-if="['static', 'config', 'desec'].includes(config.dns_mode)" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. <br>
			<span v-if="config.dns_mode == 'static'">
				This is needed, if you configured a domain to point to your 
				NextBox in e.g., with your internet router.<br>
			</span>
			<span v-if="config.dns_mode == 'desec'">
				The domain always has to end with 
				<span class="bold">dedyn.io</span>.<br>
			</span>
			<input v-model="update.domain" type="text" class="txt">
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
			<button v-if="config.dns_mode === 'static'" type="button" @click="finalize_static()">
				<span class="icon icon-confirm" />
				Finalize Static Domain Configuration
			</button>
		</div>

		<!-- Captcha deSEC & start registration... -->
		<div v-if="config.dns_mode === 'desec'" class="section">
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
		<div v-if="config.dns_mode === 'desec_2'" class="section">
			<h2>deSEC Activation Token</h2>
			<span class="bold">The registration using your provided E-Mail was successful</span>.<br>

			You should have received an E-Mail with an activation link. Please 
			click on this link and copy the presented token into this field:<br>

			<input v-model="update.desec_token" type="text" class="txt"><br>
			<button type="button" @click="finalize_desec()">
				<span class="icon icon-confirm" />
				Finalize Dynamic DNS Configuration
			</button><br>
			<br>
			If you have not received an E-Mail this means you have already 
			been registered with this E-Mail at deSEC. If you know your password
			you can <a class="bold" href="https://desec.io/login">login here</a> and copy the 
			token from your account settings. During NextBox' automated process no 
			password is set, in order to acquire one you have to 
			<a class="bold" href="https://desec.io/reset-password">reset your password</a>.
		</div>

		<!-- Raw ddclient configuration -->
		<div v-if="['config'].includes(config.dns_mode)" class="section">
			<h2>Raw DDClient configuration</h2>
			Here you can directly configure DDClient to use any supported DynDNS service. Please find 
			the documentation for DDClient <a class="bold" href="https://ddclient.net/usage.html">here</a><br>
			<textarea v-model="update.conf" class="txtmult" /><br>

			<button type="button" @click="finalize_config()">
				<span class="icon icon-confirm" />
				Finalize Raw DDClient Configuration
			</button>
		</div>

		<!-- Done View -->
		<div v-if="config.dns_mode.endsWith('_done')" class="section">
			<h2>{{ statusTitle }} - Status</h2>
			
			<div v-if="['config_done', 'desec_done'].includes(config.dns_mode)">
				<span :class="'tag ' + status.ddclientService.state"><span :class="'tag-icon ' + status.ddclientService.icon" />
					<span class="tag-content">{{ status.ddclientService.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.ddclientService.extra }}</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done', 'static_done'].includes(config.dns_mode)">
				<span :class="'tag ' + status.ddclientTest.state"><span :class="'tag-icon ' + status.ddclientTest.icon" />
					<span class="tag-content">{{ status.ddclientTest.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.ddclientTest.extra }}</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done'].includes(config.dns_mode)">
				<span :class="'tag ' + status.resolve.state"><span :class="'tag-icon ' + status.resolve.icon" />
					<span class="tag-content">{{ status.resolve.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.resolve.extra }}</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done', 'static_done'].includes(config.dns_mode)">
				<span :class="'tag ' + status.http.state"><span :class="'tag-icon ' + status.http.icon" />
					<span class="tag-content">{{ status.http.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.http.extra }}</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done', 'static_done'].includes(config.dns_mode)">
				<span :class="'tag ' + status.https.state"><span :class="'tag-icon ' + status.https.icon" />
					<span class="tag-content">{{ status.https.content }}</span>
					<span class="tag-middle" />
					<span class="tag-extra">{{ status.https.extra }}</span>
				</span>
			</div>

			<div v-if="status.help">
				{{ status.help }}
			</div>
		</div>

		<!-- Restart dynamic dns configuration -->
		<div v-if="config.dns_mode !== 'off'" class="section">
			<ActionButton
				class="bold restart-button"
				:icon="(loading) ? 'icon-loading' : 'icon-close'"
				@click="restart_config()">
				Restart Dynamic DNS Configuration
			</ActionButton>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
import Actions from '@nextcloud/vue/dist/Components/Actions'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'


export default {
	name: 'DynDNS',

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
			userMessage: {},
			
			config: {
				dns_mode: 'off',
				conf: '',
				domain: '',
				email: '',
			},
			
			status: {
				ddclientTest: { state: 'neutral', icon: 'icon-info', content: 'DDClient test pending', extra: '' },
				ddclientService: { state: 'neutral', icon: 'icon-info', content: 'DDClient service state unknown', extra: '' },
				http: { state: 'neutral', icon: 'icon-info', content: 'Reachability of Nextcloud instance unknown', extra: '' },
				resolve: { state: 'neutral', icon: 'icon-info', content: 'DNS resolve testing pending', extra: '' },
				https: { state: 'neutral', icon: 'icon-info', content: 'HTTPS waiting to be tested', extra: '' },

				intervalHandle: null,
				useIpType: 'ipv6',
				mode: 'init',
				nextMode: 'init',
				lastMode: '',
				lastModeRepeated: 0,
				waitFor: 0,
				waitCallback: null, 
				help: '',
			},

			// consts/texts
			ttConfig: 'Choose this, if you have a custom ddclient configuration you want to be used. '
					+ 'This enables the use of any Dynamic DNS provider supported by ddclient.',
			ttStatic: 'If you have a domain already configured (e.g., using your internet router), '
					+ 'choose this option to configure Nextcloud to use this domain.',
			ttDesec: 'Guide you through the process of setting up a dynamic DNS for your Nextbox. '
					+ 'This is the recommended option for most users.',

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
		statusTitle() {
			if (this.config.dns_mode === 'desec_done') {
				return 'deSEC Dynamic DNS Configuration'
			} else if (this.config.dns_mode === 'static_done') {
				return 'Static Domain Configuration'
			} else if (this.config.dns_mode === 'config_done') {
				return 'Raw DDClient Configurtation'
			} else {
				return ''
			}
		},
	},

	async mounted() {
		await this.refresh()
		if (this.config.dns_mode.endsWith('_done')) {
			await this.init_status()
		}
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

		async refresh_captcha() {
			const captchaUrl = generateUrl('/apps/nextbox/forward/dyndns/captcha')
			const captchaRes = await axios.post(captchaUrl).catch((e) => {
				showError('Cannot aquire captch from deSEC')
				console.error(e)
			})
			this.update.captcha_png = `data:image/png;base64,${captchaRes.data.data.challenge}`
			this.update.captcha_id = captchaRes.data.data.id
			this.update.captcha = ''
		},

		async init_status() {
			this.intervalHandle = window.setInterval(this.refresh_status, 1000)
			//showMessage('STAAAAART STATUS maaan')
		},

		async refresh_status() {
			if (!this.status.fsmActive) {
				this.status.fsmActive = true

				if (this.status.mode !== 'wait') {
					this.status.lastModeRepeated = (this.status.lastMode === this.status.mode) 
						? this.status.lastModeRepeated + 1 
						: 0

					this.status.lastMode = this.status.mode
				}

				if (this.status.lastModeRepeated > 20) {
					showError(`In state: ${this.status.lastMode} stalled - aborting...`)
					this.status.mode = 'fail'
					// here add help text
					this.status.help = 'we failed, this is the help text...'
				}

				//showMessage(`fsm tick - ${this.status.mode}`)
				
				switch (this.status.mode) {
				case 'init':
					await this.refresh_status_test_ddclient()
					break
				case 'wait':
					this.status.waitFor -= 1
					if (this.status.waitCallback) this.status.waitCallback(this, this.status.waitFor)
					
					if (this.status.waitFor <= 0) {
						this.status.mode = this.status.nextMode
						this.status.waitCallback = null
					}
					
					break
				case 'service':
					await this.refresh_status_test_service()
					break
				case 'start-service':
					this.status.ddclientService.icon = 'icon-loading-small'
					await this.restart_ddclient()
					this.status.mode = 'service'
					break
				case 'resolve6':
					await this.refresh_status_test_resolve('ipv6')
					break
				case 'resolve4':
					await this.refresh_status_test_resolve('ipv4')
					break
				case 'https':
					await this.refresh_status_test_reachable('https')
					break
				case 'https-enable':
					await this.enable_https()
					break
				case 'http':
					await this.refresh_status_test_reachable('http')
					break
				case 'reload':
					window.location.assign(`${(this.config.https) ? 'https' : 'http'}://${this.config.domain}/index.php/apps/nextbox/`)
					break
				case 'done':
					window.clearInterval(this.intervalHandle)
					break
				case 'fail':
					window.clearInterval(this.intervalHandle)
					showError('failed...')
					break
				}
				this.status.fsmActive = false
				
			}
		},

		async refresh_status_test_ddclient() {
			const url = '/apps/nextbox/forward/dyndns/test/ddclient'
			this.status.ddclientTest.icon = 'icon-loading-small'
			await axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.result === 'success') {
						this.status.ddclientTest.state = 'success'
						this.status.ddclientTest.content = 'DDClient updating dynamic DNS entry successful'
						this.status.ddclientTest.icon = 'icon-add'
						this.status.mode = 'service'
					} else {
						if (res.data.data.reason === 'throttled') {
							this.status.ddclientTest.icon = 'icon-loading-small'
							this.status.waitFor = parseInt(res.data.data.waitfor) + 10
							this.status.mode = 'wait'
							this.status.nextMode = 'init'
							this.status.waitCallback = function(myThis, secs) {
								myThis.status.ddclientTest.extra = (secs <= 0) ? '' : `throttled, retry in ${secs} secs`
							}
						} else {
							this.status.ddclientTest.content = 'Unknown error during DDClient test'
							this.status.ddclientTest.icon = 'icon-close'
							this.status.mode = 'fail'
						}
					}
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.ddclientTest.content = 'DDClient Test - Connection failed - aborting...'
					this.status.ddclientTest.state = 'error'
					this.status.ddclientService.icon = 'icon-close'
					this.status.mode = 'fail'
				})

			return this.status.ddclientTest.state
		},

		async refresh_status_test_reachable(what) {
			// what \in { 'https', 'http' }
			const url = '/apps/nextbox/forward/dyndns/test/' + what
			this.status[what].icon = 'icon-loading-small'
			await axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.result === 'success') {
						this.status[what].state = 'success'
						this.status[what].content = `Your Nextcloud is reachable using: ${what}://${this.config.domain}`
						this.status[what].icon = 'icon-add'
						this.status.mode = (what === 'http') ? 'https' : 'done'
					} else {
						this.status[what].state = 'warning'
						this.status[what].content = `Your Nextcloud is NOT reachable using: ${what}://${this.config.domain}`
						this.status[what].icon = 'icon-loading-small'
						
						// failed reachability for http
						if (what === 'http') {
							this.status.nextMode = 'http'
							this.status.waitFor = 10
							this.status.mode = 'wait'
							this.status.waitCallback = function(myThis, secs) {
								myThis.status.http.extra = (secs <= 0) ? '' : `retry in ${secs} secs`
							}
						} else {
						
							// we fail https, so activate it now:
							if (!this.config.https) {
								this.status.mode = 'https-enable'
								this.status[what].content = 'HTTPS is not enabled - enabling now!'
							
							// we have https activated, retry ...
							} else {
								this.status.nextMode = 'https'
								this.status.waitFor = 10
								this.status.mode = 'wait'
								this.status.waitCallback = function(myThis, secs) {
									myThis.status.https.extra = (secs <= 0) ? '' : `retry in ${secs} secs`
								}
							}
						}
					}

				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status[what].state = 'error'
					this.status[what].content = what + ' - connection failed - aborting'
					this.status[what].icon = 'icon-close'
					this.status.mode = 'fail'
				})
			return this.status[what].state
		},

		async refresh_status_test_service() {
			const url = '/apps/nextbox/forward/service/ddclient/is-active'
			this.status.ddclientService.icon = 'icon-loading-small'
			await axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.data.output[0] === 'active') {
						this.status.ddclientService.state = 'success'
						this.status.ddclientService.content = 'DDClient service is active'
						this.status.ddclientService.icon = 'icon-add'
						this.status.mode = (this.status.useIpType === 'ipv6') ? 'resolve6' : 'resolve4'
					} else {
						this.status.ddclientService.state = 'warning'
						this.status.ddclientService.content = 'DDClient service not running, restarting...'
						this.status.ddclientService.icon = 'icon-loading-small'
						this.status.mode = 'start-service'
					}
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.ddclientService.state = 'error'
					this.status.ddclientService.icon = 'icon-close'
					this.status.ddclientService.content = 'DDClient Service - Connection failed - aborting'
					this.status.mode = 'fail'
				})
			return this.status.ddclientService.state
		},
		
		async refresh_status_test_resolve(ipType) {
			const url = `/apps/nextbox/forward/dyndns/test/resolve/${ipType}`
			const ipTypeName = (ipType === 'ipv4') ? 'IPv4' : 'IPv6'
			this.status.resolve.icon = 'icon-loading-small'
			await axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.result === 'success') {
						this.status.resolve.state = 'success'
						this.status.resolve.content = `Domain ${this.config.domain} resolves to your ${ipTypeName}: ${res.data.data.ip}`
						this.status.resolve.icon = 'icon-add'
						this.status.mode = 'http'
					} else {
						this.status.resolve.state = 'warning'
						this.status.resolve.content = `Configured domain ${this.config.domain} resolves incorrectly ${ipTypeName}: ${res.data.data.ip}`
						this.status.resolve.icon = 'icon-loading-small'
						if (this.status.useIpType === 'ipv6') {
							this.status.nextMode = 'resolve6'
							//this.status.useIpType = 'ipv6'
							this.status.waitFor = 10
							this.status.mode = 'wait'
							this.status.waitCallback = function(myThis, secs) {
								myThis.status.resolve.extra = (secs <= 0) ? '' : `retry in ${secs} secs`
							}
						} else {
							this.status.nextMode = 'resolve4'
							//this.status.useIpType = 'ipv4'
							this.status.waitFor = 10
							this.status.mode = 'wait'
							this.status.waitCallback = function(myThis, secs) {
								myThis.status.resolve.extra = (secs <= 0) ? '' : `retry in ${secs} secs`
							}
						}
					}
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.resolve.state = 'error'
					this.status.resolve.content = 'Resolve Domain to IP - Connection failed - aborting'
					this.status.resolve.icon = 'icon-close'
					this.status.mode = 'fail'
				})
			return this.status.resolve.state
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

		async restart_config() {
			this.update.dns_mode = 'off'
			this.update_dns_mode()
			this.refresh()
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
			if ('domain' in this.userMessage) delete this.userMessage.domain

			return true
		},

		async update_dns_mode() {
			this.userMessage = {}
			this.update_config({ dns_mode: this.update.dns_mode })
		},

		async finalize_static() {
			if (!this.check_email()) {
				return false
			}

			this.update_config({ 
				domain: this.update.domain,
				email: this.update.email,
				dns_mode: 'static_done',
			})
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

.dns_radio {
	width: fit-content;
	display: block !important;
}

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
