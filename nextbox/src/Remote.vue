<template>
	<div class="remote">
		<!-- Done View -->
		<div v-if="config.dns_mode !== 'off' || config.proxy_active" class="section">
			<h2>Remote Access - Status</h2>
			
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
				<li v-tooltip="ttProxy" class="remote-action" @click="$emit('newPage', 'remote_proxy')">
					<span class="remote-icon icon-star" />
					Quickstart Configuration (recommended)
				</li>
				<li v-tooltip="ttDesec" class="remote-action" @click="$emit('newPage', 'remote_dyndns')">
					<span class="remote-icon icon-comment" />
					Guided Dynamic DNS Configuration (DeSEC)
				</li>
				<li v-tooltip="ttConfig" class="remote-action" @click="$emit('newPage', 'remote_custom_dns')">
					<span class="remote-icon icon-settings" />
					Custom Dynamic DNS Configuration
				</li>
				<li v-tooltip="ttStatic" class="remote-action" @click="$emit('newPage', 'remote_static_dns')">
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
	name: 'Remote',

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
				proxy_active: false,
			},
			
			status: {
				ddclientTest: { state: 'neutral', icon: 'icon-info', content: 'DDClient test pending', extra: '' },
				ddclientService: { state: 'neutral', icon: 'icon-info', content: 'DDClient service state unknown', extra: '' },
				http: { state: 'neutral', icon: 'icon-info', content: 'Reachability of Nextcloud instance unknown', extra: '' },
				resolve: { state: 'neutral', icon: 'icon-info', content: 'DNS resolve testing pending', extra: '' },
				https: { state: 'neutral', icon: 'icon-info', content: 'HTTPS waiting to be tested', extra: '' },
				proxy: { state: 'neutral', icon: 'icon-info', content: 'Quickstart remote access test pending', extra: '' },

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
					+ 'This should be the prefered option, apart from the Quickstart configuration.',
			ttProxy: 'The easiest and fastest way to get remote access for your personal Nextcloud up and running!',

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
		if (this.config.dns_mode.endsWith('_done')) {
			//await this.init_status()
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
			
			if (this.config.proxy_active) {
				this.refresh_status_test_proxy()
			}
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

		async refresh_status_test_proxy() {
			const url = '/apps/nextbox/forward/dyndns/test/proxy'
			this.status.proxy.icon = 'icon-loading-small'
			await axios.get(generateUrl(url))
				.then((res) => {
					if (res.data.result === 'success') {
						this.status.proxy.state = 'success'
						this.status.proxy.content = `Your Nextcloud is reachable via: https://${this.config.proxy_domain}`
						this.status.proxy.icon = 'icon-add'
					} else {
						this.status.proxy.state = 'error'
						this.status.proxy.content = `Your Nextcloud is NOT reachable using: https://${this.config.proxy_domain}`
						this.status.proxy.icon = 'icon-close'
					}
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
		},

		async refresh_status_test_reachable(what) {
			// what \in { 'https', 'http'}
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

		async restart_config() {
			this.update.dns_mode = 'off'
			this.update_dns_mode()
			this.refresh()
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
