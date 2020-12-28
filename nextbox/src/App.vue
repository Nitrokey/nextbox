<template>
	<div id="content" class="nextbox">
		<AppNavigation>
			<ul>
				<AppNavigationItem :title="t('nextbox', 'Overview')" icon="icon-home" @click="set_page('overview')" />
				<AppNavigationItem :title="t('nextbox', 'Storage Management')" icon="icon-category-files" @click="set_page('storage')" />
				<AppNavigationItem :title="t('nextbox', 'Backup / Restore')" icon="icon-download" @click="set_page('backup')" />
				<AppNavigationItem :title="t('nextbox', 'Dynamic DNS')" icon="icon-category-integration" @click="set_page('dyndns')" />
				<AppNavigationItem :title="t('nextbox', 'System Settings')" icon="icon-settings" @click="set_page('system')" />
				<AppNavigationItem :title="t('nextbox', 'Daemon Logs')" icon="icon-info" @click="set_page('logs')" />
			</ul>
		</AppNavigation>
		<AppContent>
			<Logs v-if="page === 'logs'" />
		</AppContent>
	</div>
</template>

<script>
// import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
// import AppNavigationNew from '@nextcloud/vue/dist/Components/AppNavigationNew'

import AppContent from '@nextcloud/vue/dist/Components/AppContent'
import AppNavigation from '@nextcloud/vue/dist/Components/AppNavigation'
import AppNavigationItem from '@nextcloud/vue/dist/Components/AppNavigationItem'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'

import Logs from './Logs'

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

export default {
	name: 'App',
	components: {
		// ActionButton, AppNavigationNew,
		AppContent,
		AppNavigation,
		AppNavigationItem,
		Logs,
	},
	data() {
		return {
			page: 'overview',
			updating: false,
			loading: true,
		}
	},
	computed: {
		/**
		 * Return the currently selected note object
		 * @returns {Object|null}
		 */
		pageaa() {
			const foo = 123
			return false //this.currentPage

		},
	},
	/**
	 * Fetch list of notes when the component is loaded
	 */
	async mounted() {
		try {
			const response = await axios.get(generateUrl('/apps/nextbox/overview'))
			// alert(response.toString())
			// his.notes = response.data

		} catch (e) {
			console.error(e)
			showError(t('nextbox', 'Could not fetch overview'))
		}
		this.loading = false
	},
	methods: {
		set_page(what) {
			this.page = what
		},
	},
}
</script>
<style scoped>
	#app-content > div {
		width: 100%;
		height: 100%;
		padding: 20px;
		display: flex;
		flex-direction: column;
		flex-grow: 1;
	}

	input[type='text'] {
		width: 100%;
	}

	textarea {
		flex-grow: 1;
		width: 100%;
	}
</style>
