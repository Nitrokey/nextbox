<template>
	<div id="logs" v-if="!loading">
		<NcAppContentDetails v-for="line in lines" :key="line">
			{{ line }}
		</NcAppContentDetails>
	</div>
</template>


<script>

import '@nextcloud/dialogs/style.css'
import { generateUrl } from '@nextcloud/router'
// import { showError, showSuccess } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import NcAppContentDetails from '@nextcloud/vue/components/NcAppContentDetails'

export default {
	name: 'Logs',
	// props: ['items'],
	components: {
		NcAppContentDetails,
	},
	data() {
		return {
			loading: true,
			lines: [],
		}
	},
	async mounted() {
		try {
			const response = await axios.get(generateUrl('/apps/nextbox/forward/log'))
			this.lines = response.data.data
		} catch (e) {
			console.error(e)
			showError(t('nextbox', 'Could not fetch logs'))
		}
		this.loading = false
	},
	methods: {
	},
}
</script>


<style scoped>
.logline { 
	color: black 
}

</style>
