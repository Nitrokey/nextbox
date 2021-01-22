<template>
	<div class="proxy">
		<div class="section">
			<h2>Quickstart Remote Access for Your NextBox</h2>
			This is by far the easiest way to make your personal Cloud available from everywhere.<br>
			Using your <span class="bold">NextBox Quickstart Token</span> you are just one click away from your private, global Nextcloud.
		</div>
		<div v-if="!config.proxy_active" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated full domain for your NextBox. The domain always has to end with <span class="bold">.nitrokey.com</span>.<br>
			<input v-model="update.proxy_domain" type="text">
			<br><span v-if="userMessage.proxy_domain" class="error-txt">{{ userMessage.proxy_domain.join(" ") }}</span><br>
			<h2>NextBox Quickstart Token</h2>
			Insert here your personal <span class="bold">NextBox Quickstart Token</span> you received together with your NextBox.<br>
			<input v-model="update.nk_token" type="text">
			<br><span v-if="userMessage.nk_token" class="error-txt">{{ userMessage.nk_token.join(" ") }}</span><br>
			<button type="button" @click="activate()">
				<span class="icon icon-confirm" />
				Activate Quickstart Remote Access
			</button>
		</div>
		<div v-else class="section">
			Your <span class="bold">NextBox Quickstart Remote Access</span> is active, you can access your Nextcloud instance
			using <a :href="'https://' + config.proxy_domain" class="bold">{{ config.proxy_domain }}</a>.<br>
			<button type="button" @click="disable()">
				<span class="icon icon-confirm" />
				Disable Quickstart Remote Access
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

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
import Actions from '@nextcloud/vue/dist/Components/Actions'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
import ActionRadio from '@nextcloud/vue/dist/Components/ActionRadio'
import ActionInput from '@nextcloud/vue/dist/Components/ActionInput'


export default {
	name: 'Proxy',

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
			userMessage: {
				nk_token: [],
				proxy_domain: [],
			},
			
			config: {
				dns_mode: 'off',
				nk_token: '',
				proxy_active: '',
				proxy_domain: '',
				
			},

			// variables
			update: {
				proxy_domain: '',
				nk_token: '',
			},
		}
	},

	computed: {

	},

	async mounted() {
		this.refresh()
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
			this.update.nk_token = this.config.nk_token
		},

		check_domain() {
			if (this.update.proxy_domain === null || !this.update.proxy_domain.includes('.')) {
				this.userMessage.proxy_domain = ['Please insert a valid domain']
				return false
			}
			if (!this.update.proxy_domain.endsWith('.nitrokey.com')) {
				this.userMessage.proxy_domain = ['The Domain has to end with: .nitrokey.com']
				return false
			}

			this.userMessage.proxy_domain = []
			return true
		},

		check_token() {
			if (this.update.nk_token === null || this.update.nk_token.length !== 20) {
				this.userMessage.nk_token = ['Please insert a valid token']
				return false
			}

			this.userMessage.nk_token = []
			return true
		},

		async activate() {
			let cont = this.check_domain()
			cont &= this.check_token()
			if (cont) {
				this.update_config({
					nk_token: this.update.nk_token,
					proxy_domain: this.update.proxy_domain,
					proxy_active: true,
				})
			}
		},

		async disable() {
			this.update_config({
				nk_token: '',
				proxy_domain: '',
				proxy_active: false,
			})
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

.proxy {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

</style>
