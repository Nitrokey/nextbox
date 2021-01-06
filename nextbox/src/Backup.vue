<template>
	<div class="backup-restore">
		<div class="section">
			<h2>Full System Backup</h2>
			You can start a full backup here. Nextcloud will change into maintainance mode and will not be available during the backup operation.
			Once the backup is started you will see a progress indicator, if you reload you won't be able to see the progress until the operation finished.
			<ActionButton
				icon="icon-download" 
				@click="start_backup">
				Start Backup now
			</ActionButton>
			<span v-if="last_backup">Your last backup was done at: <emph>{{ last_backup }}</emph></span>
			<span v-else>You have not yet run a backup - please do so!</span>
		</div>
		<div class="section">
			<Multiselect 
				:v-model="selected_backup"
				:options="backups"
				track-by="id" 
				label="label" />
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import Multiselect from '@nextcloud/vue/dist/Components/Multiselect'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'

export default {
	name: 'Backup',
	
	components: {
		Multiselect, ActionButton,
	},

	data() {
		return {
			loading: true,
			selected_backup: null,
			last_backup: new Date(),
		}
	},
	computed: {
		backups() {
			return [
				{
					id: 1, 
					label: 'foo',
				},
			]
		},
	},
	async mounted() {
		
		this.loading = false
	},

	methods: {
	},
}
</script>


<style scoped>

emph {
	font-weight: bold;
}

.backup-restore {
	display: flex;
	width: 100%;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
	margin-bottom: 24px;
}
</style>
