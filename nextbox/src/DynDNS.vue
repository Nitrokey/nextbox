<template>
	<div class="dyndns">
		<div v-if="config.dns_mode === 'off'" class="section">
			<h2>Choose a Dynamic DNS Configuration Mode</h2>
			To make your NextBox available outside of your internal network you need to configure
			a (dynamic) domain. Your Nextcloud instance will afterwards be available using this domain.
			<ActionRadio 
				v-tooltip.bottom="ttDesec" 
				@update:checked="update.dns_mode = 'desec'"
				name="dns_mode" 
				value="desec"
				class="dns_radio">
				Guided DynDNS Configuration (recommended)
			</ActionRadio>
			<ActionRadio  
				v-tooltip.bottom="ttStatic"
				@update:checked="update.dns_mode = 'static'"
				name="dns_mode" 
				value="static" 
				class="dns_radio">
				Static Domain
			</ActionRadio>
			<ActionRadio 
				v-tooltip.bottom="ttConfig" 
				@update:checked="update.dns_mode = 'config'"
				name="dns_mode" 
				value="config" 
				class="dns_radio">
				Raw DDClient Configuration
			</ActionRadio>
			<ActionButton
				:icon="(loading) ? 'icon-loading' : 'icon-confirm'"
				@click="update_dns_mode()">
				Continue
			</ActionButton>
		</div>

		<div v-if="['static', 'config', 'desec'].includes(config.dns_mode)" class="section">
			<h2>Domain for NextBox</h2>
			Insert the designated (sub)domain for your NextBox.<br>
			<!-- span class="icon icon-address" /-->
			<input type="text" class="txt" :value="update.domain">
			<button @click="update_domain()">
				<span class="icon icon-confirm" />
				Save Domain
			</button>
			<ActionButton
				:icon="(loading) ? 'icon-loading' : 'icon-play'"
				@click="false">
				Test Domain
			</ActionButton>
		</div>

		<div v-if="['static', 'config', 'desec'].includes(config.dns_mode)" class="section">
			<h2>E-Mail for DeSec Dynamic DNS Registration & Let's Encrypt</h2>
			Insert the designated (sub)domain for your NextBox.<br>
			<!-- span class="icon icon-address" /-->
			<input type="text" class="txt" :value="update.domain">
			<button @click="update_email()">
				<span class="icon icon-confirm" />
				Save E-Mail
			</button>
		</div>

		<div v-if="['config'].includes(config.dns_mode)" class="section">
			<h2>Direct DDClient configuration</h2>
			Here you can directly configure ddclient to use any supported DynDNS service. Please find 
			the documentation for DDClient <a class="bold" href="https://ddclient.net/usage.html">here</a><br>
			<!-- span class="icon icon-address" /-->
			<textarea v-model="update.conf" class="txtmult" />
			<button style="vertical-align: top" @click="update_conf()">
				<span class="icon icon-confirm" />
				Save Configuration
			</button>
			<ActionButton
				:icon="(loading) ? 'icon-loading' : 'icon-play'"
				@click="false">
				Test DDClient Configuration
			</ActionButton>
		</div>

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
			config: null,
			
			// consts/texts
			ttConfig: 'Choose this, if you have a custom ddclient configuration you want to be used. '
					+ 'This enables the use of any Dynamic DNS provider supported by ddclient.',
			ttStatic: 'If you have a domain already configured (e.g., using your internet router), '
					+ 'choose this option to configure Nextcloud to use this domain.',
			ttDesec: 'Guide you through the process of setting up a dynamic DNS for your Nextbox. '
					+ 'This is the recommended option for most users.',

			// variables
			update: {}
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
			this.update = {
				dns_mode: this.config.dns_mode,
				conf: this.config.conf,
				domain: this.config.domain,
				email: this.config.email,
			}
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


		async update_dns_mode() {
			console.error(this.update.dns_mode)
			this.update_config({ dns_mode: this.update.dns_mode })
		},
		async update_domain() {
			this.update_config({ email: this.update.email })
		},
		async update_email() {
			this.update_config({ domain: this.update.domain })
		},
		async update_conf() {
			this.update_config({ conf: this.update.conf })
		},

		async update_config(update) {
			const url = '/apps/nextbox/forward/dyndns/config'
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

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}

.section {
	display: block;
	padding: 30px;
	margin: 0;
	height: fit-content !important;
}

.icon {
	/*padding-right: 2em;*/
}

.txt {
	width: 25vw;
}

.txtmult {
	width: 25vw;
	height: 10em;
}

</style>
