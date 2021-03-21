<template>
	<div class="static_dyndns">
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
			<button type="button" @click="activate()" :disabled="activateDisabled">
				<span class="icon icon-confirm" />
				Activate Configuration
			</button>
		</div>
		<div v-else-if="config.dns_mode !== 'static_done'" class="section">
			There is an active DNS Configuration. To activate the static 
			domain configuration you have to disable your existing configuration first.
		</div>
		<div v-else class="section">
			Your StaticDNS configuration is enabled for the domain: 
			<span class="bold">{{ update.domain }}</span><br><br>
			
			<button type="button" @click="disable()">
				<span class="icon icon-confirm" />
				Disable Static Domain Configuration
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
	name: 'StaticDNS',

	components: {
		
	},

	data() {
		return {
			// generics
			loading: false,
			userMessage: {
				domain: [],
			},
			
			config: {
				dns_mode: 'off',
				domain: '',
			},
			
			// variables
			update: {
				dns_mode: 'off',
				domain: '',
			},
		}
	},

	async mounted() {
		await this.refresh()
		this.loading = false
	},

	computed: {
		activateDisabled() {
			return !this.checkDomain()
		},
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
			this.userMessage.domain = []
			return true
		},

		async activate() {
			if (this.checkDomain()) {
				this.update_config({ 
					domain: this.update.domain,
					//email: this.update.email,
					dns_mode: 'static_done',
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

.static_dyndns {
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
