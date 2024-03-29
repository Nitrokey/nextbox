<template>
	<div id="proxy" v-if="!loading">
		<div class="section">
			<h2>Backwards Proxy Remote Access for Your NextBox</h2>
			The easiest way to make your personal Cloud available from everywhere.<br>
		</div>
		
		<div v-if="!config.proxy_active" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. The domain must end with <b>.nextbox.link</b><br>
			<input v-model="update.proxy_domain" type="text" @change="checkDomain">
			<br><span v-if="userMessage.proxy_domain" class="error-txt">{{ userMessage.proxy_domain.join(" ") }}</span><br>
			<button type="button" :disabled="activateDisabled" @click="activate()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Activate Quickstart Remote Access
			</button>
		</div>

		<div v-else class="section">
			Your <b>NextBox Quickstart Remote Access</b> is
			active, you can access your Nextcloud instance using <span v-html="toLink(config.proxy_domain)" />.<br>

			<StatusBar v-if="config.proxy_active" preset="reach_proxy" /><br>

			<button type="button" :disabled="disableDisabled" @click="disable()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-close')" />
				Disable Quickstart Remote Access
			</button>
		</div>
	</div>
</template>

<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
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
import StatusBar from './StatusBar'


export default {
	name: 'Proxy',
	
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
				proxy_domain: [],
			},
			
			config: {
				dns_mode: 'off',
				proxy_active: '',
				proxy_domain: '',
				
			},

			// update-ables
			update: {
				proxy_domain: '',
			},
		}
	},

	computed: {
		activateDisabled() {
			return this.loadingButton || !this.checkDomain()
		},

		disableDisabled() {
			return this.loadingButton
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
			this.update.proxy_domain = this.config.proxy_domain
		},

		checkDomain() {
			const tld = '.nextbox.link'

			const pat = /^((?:(?:(?:\w[.\-+]?)*)\w)+)((?:(?:(?:\w[.\-+]?){0,62})\w)+)\.(\w{2,6})$/
			if (!pat.test(this.update.proxy_domain)) {
				this.userMessage.proxy_domain = ['Please insert a valid domain']
				return false
			}
			
			if (!this.update.proxy_domain.endsWith(tld)) {
				this.userMessage.proxy_domain = [`Your proxy domain must end with <b>${tld}</b>`]
				return false
			}

			const subdomain = this.update.proxy_domain.slice(0, -tld.length)
			const patSub = /^(?:[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]|[A-Za-z0-9])$/
			if (!patSub.test(subdomain)) {
				this.userMessage.proxy_domain = ['Not allowed characters in subdomain!']
				return false
			}

			if (subdomain.length < 5) {
				this.userMessage.proxy_domain = ['The subdomain has to be at least 5 characters long']
				return false
			}

			this.userMessage.proxy_domain = []
			return true
		},
		
		async activate() {
			if (this.checkDomain()) {
				this.loadingButton = true
					
				// after updating the config, register at nextbox-proxy
				const data = {
					proxy_domain: this.update.proxy_domain,
					proxy_active: true,
					nk_token: this.config.nk_token,
				}
				const url = '/apps/nextbox/forward/proxy/register'
				const options = {
					headers: { 'content-type': 'application/x-www-form-urlencoded' },
				}
				const res = await axios.post(generateUrl(url), qs.stringify(data), options)
					.then((res) => {
						if (res.data.result !== 'success') {
							showError(res.data.msg)
						} else {
							this.refresh()
							showSuccess('backwards proxy activated')
						}
					}).catch((e) => {
						showError('Connection failed')
						console.error(e)
					})
				this.loadingButton = false
			}
		},

		async disable() {
			this.loadingButton = true
			await this.update_config({
				proxy_active: false,
			})
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

			await this.refresh()
		},
	},
}
</script>


<style scoped>

.dns_radio {
	width: fit-content;
	display: block !important;
}

#proxy {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

</style>
