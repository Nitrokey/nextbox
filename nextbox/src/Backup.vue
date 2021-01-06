<template>
	<div class="backup-restore">
		<div class="section">
			<h2>Full System Backup</h2>
			You can start a full backup here. Nextcloud will change into maintainance mode and will not be available during the backup operation.
			Once the backup is started you will see a progress indicator, if you reload you won't be able to see the progress until the operation finished.
			<ActionButton
				icon="icon-download" 
				@click="start_backup()">
				Start Backup now
			</ActionButton>
			<span v-if="last_backup">Your last backup was done at: <span class="bold">{{ last_backup }}</span></span>
			<span v-else class="bold"><span class="icon icon-error"></span>You have not yet run a backup - please do so<span class="icon icon-error"></span></span>
		</div>
		<div class="section">
			<h2>Restore System from Backup</h2>
			<div v-if="last_backup">
				Similar to the backup process, restoring the system from a backup will set Nextcloud into maintainance mode and you will be presented 
				with a progress indicator. 
				<br>
				<Multiselect 
					v-if="last_backup"
					:v-model="selected_backup"
					:options="backups"
					track-by="id" 
					label="label" />
				<ActionButton
					:disabled="selected_backup"
					icon="icon-upload" 
					@click="start_restore()">
					Start Restoring now
				</ActionButton>
			</div>
			<EmptyContent v-if="!last_backup" icon="icon-close">
				No Backup to restore available yet...
			</EmptyContent>
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
import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'

export default {
	name: 'Backup',
	
	components: {
		Multiselect, ActionButton, EmptyContent,
	},

	data() {
		return {
			loading: true,
			selected_backup: false,
			data: null,
		}
	},
	computed: {
		lastBackup() {
			return this.data.last_backup
		},

		backups() {
			return this.data.found.map((item) => {
				return {
					label: `${item.name} | created: ${new Date(item.created)} | size: ${item.size}B`,
					id: item.created,
				}
			})
		},
	},
	async mounted() {
		this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			const url = '/apps/nextbox/forward/backup'
			
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.data = res.data.data
		},

		async start_backup() {

		},
	},
}
</script>


<style scoped>

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
