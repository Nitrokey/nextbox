<template>
	<div class="system">
		x
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
	name: 'System',
	components: {
		AppContentDetails,
	},

	data() {
		return {
			loading: true,
			email: '',
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
				this.email = res.data.data.email
			} catch (e) {
				console.error(e)
				//showError(t('nextbox', 'Could not fetch logs'))
			}
		},


		async update_config(what) {
			const url = '/apps/nextbox/forward/config'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			try {
				const res = await axios.post(generateUrl(url), qs.stringify(what), options)
				return res.data.result === 'success'
			} catch (e) {
				showError('Connection failed')
				console.error(e)
				return false
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
