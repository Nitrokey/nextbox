<template>
	<div id="overview" v-if="!loading">
		<!-- External availability  -->
		<div class="section">
			<h2>Remote Access for Your NextBox</h2>
			<StatusBar :status="statusRemote" />
		</div>

		<!-- Last Backup  -->
		<div v-if="running" class="section">
			<h2>Last Backup</h2>
			<StatusBar :status="statusBackup" />
		</div>

		<!-- NextBox System Daemon -->
		<div class="section">
			<h2>NextBox System Daemon Status</h2>
			<StatusBar :status="statusConnection" />
			<StatusBar icon="info" :text="`NextBox Software Version: ${this.version}`" />
		</div>

		<!-- div class="section">
			<pre>
				{{ board }}
			</pre>
		</div /-->
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import axios from '@nextcloud/axios'

//import qs from 'qs'
// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import { showError, showSuccess } from '@nextcloud/dialogs'


import StatusBar from './StatusBar'


export default {
	name: 'Overview',
	components: {
		StatusBar
	},

	data() {
		return {
			loading: true,

			config: {},

			apiMatch: false,
			expectedApi: 1,
			running: false,
			board: {},
			version: '',
		}
	},

	async mounted() {
		this.refresh()
		this.loading = false
	},

	computed: {
		statusConnection() {
			const preText = 'NextBox Backend Connection'
			return {
				icon: (this.running) ? 'checkmark' : 'loading-small',
				state: (this.running) ? 'success' : 'neutral',
				text: (this.running) ? `${preText} available` : `${preText} testing`,
			}
		},

		statusRemote() {
			if (this.config.dns_mode === 'off' && !this.config.proxy_active) {
				return {
					text: 'There is no active remote access configuration',
					icon: 'info', 
					state: 'neutral',
				}
			} else {
				return {
					text: 'Your Nextbox is configured for remote access',
					icon: 'checkmark',
					state: 'success',
				}
			}
		},

		statusBackup() {
			return {
				state: (this.config.last_backup) ? 'success' : 'warning',
				icon: (this.config.last_backup) ? 'checkmark' : 'close',
				text: (this.config.last_backup) 
					? `Your last backup was done at: ${new Date(this.config.last_backup * 1e3).toLocaleString()}`
					: 'You have not yet run a backup - please do so',
			}
		},
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
			this.statusBoard()
		},

		async statusBoard() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/status'))
				this.board = JSON.stringify(res.data, null, 2)
				this.version = res.data.data.pkginfo.version
			} catch (e) {
				console.error('failed loading status board')
			}
		},
	},
}
</script>


<style scoped>

#overview {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

</style>
