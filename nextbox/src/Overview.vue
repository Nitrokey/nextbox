<template>
	<div class="overview">
		<!-- External availability  -->
		<div class="section">
			<h2>External Reachability of Your NextBox</h2>
			Work in progress....<br>
			Show information about: dyndns-working (ddclient active), nextcloud reachable through configured domain<br>
		</div>

		<!-- Last Backup  -->
		<div v-if="running" class="section">
			<h2>Last Backup</h2>
			<span v-if="config.last_backup" class="tag success"><span class="icon icon-checkmark" />Your last backup was done at: <span class="bold">{{ new Date(config.last_backup * 1e3).toLocaleString() }}</span></span>
			<span v-else class="tag warning"><span class="icon icon-close" />You have not yet run a backup - please do so</span>
		</div>

		<!-- NextBox System Daemon -->
		<div class="section">
			<h2>NextBox System Daemon Status</h2>

			<span v-if="running" class="tag success"><span class="icon icon-checkmark" />The Backend is up and running</span>
			<span v-else class="tag error"><span class="icon icon-error" />Cannot connect to the Backend</span>
			
			<span v-if="apiMatch" class="tag success"><span class="icon icon-checkmark" />The Backend & Frontend API versions match</span>
			<span v-else class="tag error"><span class="icon icon-error" />The Backend & Frontend API version <span class="bold">do not match</span> - update both!</span>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'

export default {
	name: 'Overview',
	components: {
		AppContentDetails,
	},

	data() {
		return {
			loading: true,
			config: {},
			apiMatch: false,
			expectedApi: 1,
			running: false,
		}
	},

	async mounted() {
		this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/config'))
				this.config = res.data.data
				this.apiMatch = res.data.api === this.expectedApi
				this.running = true
			} catch (e) {
				console.error(e)
				//showError(t('nextbox', 'Could not fetch logs'))
				this.config = {}
				this.apiMatch = false
				this.running = false
			}
		},
	},
}
</script>


<style scoped>

.overview {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

</style>
