<template>
	<div class="tls">
		<div class="section">
			<h2>HTTPS / TLS Configuration</h2>
			<EmptyContent v-if="!config.email" icon="icon-close">
				To enable HTTPS / TLS you need to provide a valid E-Mail address 
				inside the <span class="bold">System Settings</span> to be used 
				for the Let's Encrypt registration.
			</EmptyContent>
			<EmptyContent v-else-if="!config.dns_mode.endsWith('_done')" icon="icon-close">
				In order to activate TLS encryption for your Nextcloud instance, 
				first finish a DNS Configuration.
			</EmptyContent>
			<div v-else>
				<div v-if="config.https_port">
					<span class="tag success"><span class="icon icon-checkmark" />
						HTTPS / TLS is activated, your Nextcloud is available via 
						<a :href="'https://' + config.domain">{{ config.domain }}</a>
					</span><br>
					<button v-tooltip="ttDisable" type="button" @click="disable()">
						<span class="icon icon-confirm" />
						Disable HTTPS
					</button>
				</div>
				<div v-else>
					<span class="tag warning"><span class="icon icon-error" />
						HTTPS / TLS is not activated
					</span><br>
					<button v-tooltip="ttEnable" type="button" @click="enable()">
						<span class="icon icon-confirm" />
						Enable HTTPS 
					</button>
				</div><br>
				Enabling or Disabling HTTPS might need a restart of your Browser to properly
				access your Nextcloud afterwards as caching sometimes leads to issues.
			</div>
		</div>
		<Modal v-if="overlay" dark @close.prevent="">
			<div class="modal-box">
				<span class="bold">{{ overlayText }}</span>
			</div>
		</Modal>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'
import Modal from '@nextcloud/vue/dist/Components/Modal'

export default {
	name: 'TLS',
	
	components: {
		EmptyContent,
		Modal,
	},

	data() {
		return {
			overlay: false,
			overlayText: '',
			config: {},
			
			// consts/texts
			ttEnable: 'This will use your e-mail address to register a certificate '
					+ 'at Let\'s Crypt and install it to your NextBox\' Nextcloud instance. '
					+ 'Afterwards your NextBox shall be available using HTTPS.',
			ttDisable: 'Disabling HTTPS will remove the currently used certificate.'
					 + 'Your NextBox will only be available without encryption using http',
		}
	},

	async mounted() {
		await this.refresh()
	},

	methods: {
		async refresh() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/config'))
				this.config = res.data.data
			} catch (e) {
				console.error(e)
				showError(t('nextbox', 'Connection Failed'))
			}
			this.overlay = false
		},

		async enable() {
			this.overlay = true
			this.overlayText = 'Enabling HTTPS - please wait...'
			const url = '/apps/nextbox/forward/https/enable'
			/*const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}*/
			const res = await axios.post(generateUrl(url)) //, qs.stringify(update)) //, options)
				.then((res) => {
					this.overlayText = 'Enabled HTTPS, please reload your browser'
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
		},

		async disable() {
			this.overlay = true
			this.overlayText = 'Disable HTTPS - please wait...'
			const url = '/apps/nextbox/forward/https/disable'
			/*const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}*/
			const res = await axios.post(generateUrl(url)) //, qs.stringify(update)) //, options)
				.then((res) => {
					this.overlayText = 'Enabled HTTPS, please reload your browser'
				}).catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
		},
	},
}
</script>


<style scoped>

.tls {
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
