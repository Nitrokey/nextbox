<template>
	<div id="static_dyndns" v-if="!loading">
		<div class="section">
			<h2>Static Domain Configuration</h2>
			This is needed, if you configured a domain to point to your 
			NextBox in e.g., using dynamic DNS on your internet router.
		</div>
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox.<br>
			<input v-model="update.domain" 
				type="text" 
				class="txt" 
				@change="checkDomain()">
			<br><span v-if="userMessage.domain" class="error-txt">{{ userMessage.domain.join(" ") }}</span><br>
			<button type="button" :disabled="activateDisabled" @click="activate()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Activate Configuration
			</button>
		</div>
		<div v-else-if="config.dns_mode !== 'static_done'" class="section">
			There is an active DNS Configuration. To activate the static 
			domain configuration you have to disable your existing configuration first.
		</div>
		<div v-else class="section">
			<StatusBar v-if="config.domain" preset="resolve_ipv4" />
			<StatusBar v-if="config.domain" preset="resolve_ipv6" /><br>
			This DNS configuration is active for the domain: <span class="bold">{{ update.domain }}</span><br><br>
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

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
// import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
// import Actions from '@nextcloud/vue/dist/Components/Actions'
// import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
// import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
// import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'

import StatusBar from './StatusBar'


export default {
	name: 'StaticDNS',

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
			},
			
			config: {
				dns_mode: 'off',
				domain: '',
				https_port: false,
			},
			
			// variables
			update: {
				dns_mode: 'off',
				domain: '',
			},
		}
	},

	computed: {
		activateDisabled() {
			return this.loadingButton || !this.checkDomain()
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
		},

		async disable() {
			this.update_config({
				//domain: '',
				dns_mode: 'off',
			})
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

		async activate() {
			if (this.checkDomain()) {
				this.loadingButton = true
				await this.update_config({ 
					domain: this.update.domain,
					dns_mode: 'static_done',
				})
				this.loadingButton = false
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

#static_dyndns {
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
