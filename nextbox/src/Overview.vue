<template>
	<div class="overview">
		<!-- External availability  -->
		<div class="section">
			<h2>External Reachability of Your NextBox</h2>
			Show information about: dyndns-working (ddclient active), nextcloud reachable through configured domain
		</div>

		<!-- Last Backup  -->
		<div class="section">
			<h2>Last Backup</h2>
			<span v-if="lastBackup">Your last backup was done at: 
				<span class="bold">{{ new Date(lastBackup * 1e3).toLocaleString() }}</span>
			</span>
			<span v-else class="bold">
				<span class="icon icon-error" />
				You have not yet run a backup - please do so
				<span class="icon icon-error" />
			</span>
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
			} catch (e) {
				console.error(e)
				//showError(t('nextbox', 'Could not fetch logs'))
			}
		},
	},
}
</script>


<style scoped>

.system {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

.icon {
	width: 44px;
	height: 44px;
	opacity: 1;
	background-position: 14px bottom;
	background-size: 16px;
	background-repeat: no-repeat;
	display: inline-block;
	vertical-align: text-bottom;
}

.section {
	display: block;
	padding: 30px;
	margin: 0;
	height: fit-content !important;
}

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}

.txt {
	width: 25vw;
}

</style>
