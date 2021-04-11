<template>
	<div class="overview">
		<!-- External availability  -->
		<div class="section">
			<h2>Remote Access for Your NextBox</h2>
			<span :class="'tag ' + status.remote.state"><span :class="'tag-icon ' + status.remote.icon" />
				<span class="tag-content">{{ status.remote.content }}</span>
				<span class="tag-middle" />
				<span class="tag-extra">{{ status.remote.extra }}</span>
			</span>
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
			
			<span class="tag neutral"><span class="icon icon-checkmark" />NextBox Software Version: {{ version }}</span>
			
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



export default {
	name: 'Overview',
	components: {
	},

	data() {
		return {
			loading: true,
			config: {},
			apiMatch: false,
			expectedApi: 1,
			running: false,

			status: {
				remote: { 
					state: 'neutral', 
					icon: 'icon-info', 
					content: '', 
					extra: '',
				},
			},

			board: {},
			version: '',
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
			this.statusRemote()
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

		async statusRemote() {
			if (this.config.dns_mode === 'off' && !this.config.proxy_active) {
				this.status.remote = {
					content: 'There is no active remote access configuration',
					icon: 'icon-info', 
					state: 'neutral',
				}
			} else {
				this.status.remote = {
					content: 'Your Nextbox is configured for remote access',
					icon: 'icon-checkmark',
					state: 'success',
				}
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
