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
			</ActionRadio>
			<ActionButton
				:disabled="noEmail && update.dns_mode == 'desec'"
				:icon="(loading) ? 'icon-loading' : 'icon-confirm'"
				@click="update_dns_mode()">
				Continue
			</ActionButton><br>
			<span v-if="noEmail && update.dns_mode == 'desec'" class="error-txt">
				For guided dynamic DNS configuration, please first set a valid 
				E-Mail address in the <span class="bold">System Settings</span>.
			</span>
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
			<!-- button v-if="config.dns_mode !== 'desec'" type="button" @click="update_domain()">
				<span class="icon icon-confirm" />
				Save Domain
			</button -->
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
			<!--ActionButton v-if="config.dns_mode == 'desec'"
				:icon="(loading) ? 'icon-loading' : 'icon-play'"
				@click="check_desec_domain()">
				Test Domain Availability
			</ActionButton_ -->
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
			you can <a href="https://desec.io/login">login here</a> and copy the 
			token from your account settings. During NextBox' automated process no 
			password is set, in order to acquire one you have to 
			<a href="https://desec.io/reset-password">reset your password</a>.
		</div>

		<!-- Raw ddclient configuration -->
		<div v-if="['config'].includes(config.dns_mode)" class="section">
			<h2>Raw DDClient configuration</h2>
			Here you can directly configure DDClient to use any supported DynDNS service. Please find 
			the documentation for DDClient <a class="bold" href="https://ddclient.net/usage.html">here</a><br>
			<textarea v-model="update.conf" class="txtmult" /><br>
			<!-- button style="vertical-align: top" type="button" @click="update_conf()">
				<span class="icon icon-confirm" />
				Save Configuration
			</button -->
			<button type="button" @click="finalize_config()">
				<span class="icon icon-confirm" />
				Finalize Raw DDClient Configuration
			</button>
			<!--ActionButton
				:icon="(loading) ? 'icon-loading' : 'icon-play'"
				@click="false">
				Test DDClient Configuration
			</ActionButton -->
		</div>

		<!-- Done View -->
		<div v-if="config.dns_mode.endsWith('_done')" class="section">
			<h2>{{ statusTitle }} - Status</h2>
			
			<div v-if="['config_done', 'desec_done'].includes(config.dns_mode)">
				<span v-if="status.ddclientService" class="tag success"><span class="icon icon-checkmark" />The DDClient Service is Active</span>
				<span v-else>
					<span class="tag error"><span class="icon icon-error" />DDClient Service not running</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done', 'static_done'].includes(config.dns_mode)">
				<span v-if="status.domain === null" class="tag neutral"><span class="icon icon-info" />Not available via <a :href="'http://' + config.domain">{{ config.domain }}</a> - testing DDClient...</span>
				<span v-else-if="status.domain" class="tag success"><span class="icon icon-checkmark" />Your NextBox is available via <a :href="'http://' + config.domain">{{ config.domain }}</a></span>
				<span v-else>
					<span class="tag error"><span class="icon icon-error" />Your NextBox is currently not available via <a :href="'http://' + config.domain">{{ config.domain }}</a></span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done', 'static_done'].includes(config.dns_mode)">
				<span v-if="status.resolve === null" class="tag neutral"><span class="icon icon-info" />
					Domain: <span class="bold">{{ config.domain }}</span> not resolving to external IP: <span class="bold">{{ status.ip }}</span> - testing DDClient...
				</span>
				<span v-else-if="status.resolve" class="tag success"><span class="icon icon-checkmark" />
					Your configured Domain: <span class="bold">{{ config.domain }}</span> correctly resolves to your external IP: <span class="bold">{{ status.ip }}</span>
				</span>
				<span v-else>
					<span class="tag error"><span class="icon icon-error" />
						Your configured Domain: <span class="bold">{{ config.domain }}</span> does not resolve to your external IP: <span class="bold">{{ status.ip }}</span>
					</span>
				</span>
			</div>

			<div v-if="['config_done', 'desec_done'].includes(config.dns_mode)">
				<span v-if="status.ddclientTest === null" class="tag neutral"><span class="icon icon-info" />DDClient Configuration Test - Not Needed</span>
				<span v-else-if="status.ddclientTest" class="tag success"><span class="icon icon-checkmark" />DDClient Configuration Test Successful</span>
				<span v-else>
					<span class="tag error"><span class="icon icon-error" />
						DDClient Configuration Test has failed! {{ status.ddclientTestDetails && status.ddclientTestDetails.desc }}
					</span>
				</span>
			</div>
		</div>

		<!-- Restart dynamic dns configuration -->
		<div v-if="config.dns_mode !== 'off'" class="section">
			<ActionButton
				class="bold"
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
				ddclientTest: null,
				ddclientTestDetails: {},
				ddclientService: false,
				domain: false,
				resolve: false,
				ip: '',
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
			},
		}
	},

	computed: {
		noEmail() {
			return !this.config.email
		},
		userMessageCaptcha() {
			console.error('userMessageCaptcha', this.userMessage)
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
			await this.refresh_status()
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

		async refresh_status() {
			await this.refresh_status_test_domain()
			await this.refresh_status_test_service()
			await this.refresh_status_test_resolve()
			if (!this.status.resolve) {
				this.status.resolve = null
				this.status.domain = null
				await this.refresh_status_test_ddclient()
				if (!this.status.ddclientTest) {
					await this.refresh_status_test_resolve()
					await this.refresh_status_test_domain()
				}
			}
		},

		async refresh_status_test_ddclient() {
			const url1 = '/apps/nextbox/forward/dyndns/test/ddclient'
			await axios.get(generateUrl(url1))
				.then((res) => {
					this.status.ddclientTest = res.data.result === 'success'
					this.status.ddclientTestDetails = res.data.data
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.ddclientTest = false
				})

			if (!this.status.ddclientTest) {
				window.setTimeout(function() {
					axios.get(generateUrl(url1))
						.then((res) => {
							this.status.ddclientTest = res.data.result === 'success'
							this.status.ddclientTestDetails = res.data.data
						}).catch((e) => {
							showError('Connection failed')
							console.error(e)
							this.status.ddclientTest = false
						})
				}, 1000)
			}
				


		},
		async refresh_status_test_domain() {
			const url2 = '/apps/nextbox/forward/dyndns/test/domain'
			await axios.get(generateUrl(url2))
				.then((res) => {
					this.status.domain = res.data.result === 'success'
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.domain = false
				})
		},
		async refresh_status_test_service() {
			const url3 = '/apps/nextbox/forward/service/ddclient/is-active'
			await axios.get(generateUrl(url3))
				.then((res) => {
					this.status.ddclientService = res.data.data.output[0] === 'active'
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.ddclientService = false
				})
		},
		async refresh_status_test_resolve() {
			const url4 = '/apps/nextbox/forward/dyndns/test/resolve'
			await axios.get(generateUrl(url4))
				.then((res) => {
					this.status.resolve = res.data.result === 'success'
					this.status.ip = res.data.data.ip  
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
					this.status.resolve = false
					this.status.ip = ''
				})
		},

		async restart_config() {
			this.update.dns_mode = 'off'
			this.update_dns_mode()
			this.refresh()
		},

		async update_dns_mode() {
			this.userMessage = {}
			this.update_config({ dns_mode: this.update.dns_mode })
		},

		async finalize_static() {
			this.update_config({ 
				domain: this.update.domain,
				dns_mode: 'static_done',
			})
		},

		async finalize_config() {
			this.update_config({ 
				conf: this.update.conf,
				domain: this.update.domain,
				dns_mode: 'config_done',
			})
			this.restart_ddclient()
		},

		async finalize_desec() {
			if (this.update.desec_token.length !== 28) {
				showError('The token is not valid')
				return
			}

			const ddclientConfig = 'protocol=dyndns2\n'
			+ 'use=web, web=https://checkipv4.dedyn.io/\n'
			+ 'ssl=yes\n'
			+ 'server=update.dedyn.io\n'
			+ `login='${this.config.domain}'\n`
			+ `password='${this.update.desec_token}'\n`
			+ `${this.config.domain}\n`

			this.update_config({ 
				desec_token: this.update.desec_token, 
				dns_mode: 'desec_done',
				conf: ddclientConfig,
			})
			await this.restart_ddclient()
			this.refresh_status()
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
			} else {
				this.update_config({
					dns_mode: 'desec_2',
					domain: this.update.domain,
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
			//showMessage(Object.keys(this.configUpdate).map((k) => `${k}: ${this.configUpdate[k]}`).join('\n'))
			this.refresh()
		},
	},
}
</script>


<style scoped>

.dns_radio {
	width: fit-content;
}

.dyndns {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
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
