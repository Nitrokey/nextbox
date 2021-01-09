<template>
	<div class="dyndns">
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Choose a Dynamic DNS Configuration Mode</h2>
			To make your NextBox available outside of your internal network you need to configure
			a (dynamic) domain. Your Nextcloud instance will afterwards be available using this domain.
			<ActionRadio v-tooltip.bottom="ttDesec" 
				name="dns_mode" 
				value="desec" 
				class="dns_radio"
				@update:checked="update_dns_mode('desec')">
				Guided DynDNS Configuration (recommended)
			</ActionRadio>
			<ActionRadio v-tooltip.bottom="ttStatic" 
				name="dns_mode" 
				value="static" 
				class="dns_radio"
				@update:checked="update_dns_mode('static')">
				Static Domain
			</ActionRadio>
			<ActionRadio v-tooltip.bottom="ttConfig" 
				name="dns_mode" 
				value="config" 
				class="dns_radio"
				@update:checked="update_dns_mode('config')">
				Raw DDClient Configuration
			</ActionRadio>
			<ActionButton
				:icon="(loading) ? 'icon-loading' : 'icon-confirm'"
				@click="update_config()">
				Continue
			</ActionButton>
		</div>

		<div v-if="config.dns_mode !== 'off'" class="section">
			<ActionButton
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


export default {
	name: 'DynDNS',

	components: {
		AppContentDetails,
		Actions,
		ActionRadio,
		ActionButton,
	},

	data() {
		return {
			loading: false,
			config: false,
			configUpdate: {},
			ttConfig: 'Choose this, if you have a custom ddclient configuration you want to be used. '
					+ 'This enables the use of any Dynamic DNS provider supported by ddclient.',
			ttStatic: 'If you have a domain already configured (e.g., using your internet router), '
					+ 'choose this option to configure Nextcloud to use this domain.',
			ttDesec: 'Guide you through the process of setting up a dynamic DNS for your Nextbox. '
					+ 'This is the recommended option for most users.',
		}
	},

	async mounted() {
		await this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			const url = '/apps/nextbox/forward/dyndns/config'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.config = res.data.data
		},

		update_dns_mode(mode) {
			this.configUpdate.dns_mode = mode
		},

		async restart_config() {
			const url = '/apps/nextbox/forward/dyndns/config'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const res = await axios.post(generateUrl(url), qs.stringify({ dns_mode: 'off' }), options)
				.catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
			this.refresh()
		},

		async update_config() {
			const url = '/apps/nextbox/forward/dyndns/config'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const res = await axios.post(generateUrl(url), qs.stringify(this.configUpdate), options)
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

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}

.section {
	display: block;
	padding: 30px;
	margin: 0;
	height: fit-content !important;
}
</style>
