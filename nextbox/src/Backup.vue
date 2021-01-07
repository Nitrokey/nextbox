<template>
	<div class="backup-restore">
		<div class="section">
			<h2>Full System Backup</h2>
			You can start a full backup here. Nextcloud will change into maintainance mode 
			and will not be available during the backup operation. Once the backup is started 
			you will see a progress indicator, if you reload you won't be able to see the 
			progress until the operation finished.
			<ActionButton
				icon="icon-download" 
				@click="start_backup()">
				Start Backup now
			</ActionButton>
			<span v-if="lastBackup">Your last backup was done at: 
				<span class="bold">{{ new Date(lastBackup * 1e3).toLocaleString() }}</span>
			</span>
			<span v-else class="bold">
				<span class="icon icon-error" />
				You have not yet run a backup - please do so
				<span class="icon icon-error" />
			</span>
		</div>

		<div class="section">
			<h2>Restore System from Backup</h2>
			<div v-if="lastBackup">
				Similar to the backup process, restoring the system from a 
				backup will set Nextcloud into maintainance mode and you 
				will be presented with a progress indicator. 
				<br>
				<Multiselect 
					v-model="selectedBackup"
					:options="backups"
					track-by="id" 
					label="label"
					style="width: 100%" />
				<ActionButton
					:disabled="selectedBackup === false"
					icon="icon-upload" 
					@click="start_restore()">
					Start Restoring now
				</ActionButton>
			</div>
			<EmptyContent v-if="!lastBackup" icon="icon-close">
				No Backup to restore available yet...
			</EmptyContent>
		</div>

		<Modal 
			v-if="overlay.active"
			v-model="overlay"
			dark
			@close="overlay.active = false">
			<div class="modal-box">
				<span class="bold">{{ overlay.text }}</span><br><br>
				<ProgressBar 
					v-if="overlay.mode == 'backup'" 
					:value="overlay.progress"
					:error="overlay.error" />
				<br>
				{{ overlay.progressStep }}
			</div>
		</Modal>
	</div>
</template>

<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess, TOAST_PERMANENT_TIMEOUT } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import Multiselect from '@nextcloud/vue/dist/Components/Multiselect'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'
import Modal from '@nextcloud/vue/dist/Components/Modal'
import ProgressBar from '@nextcloud/vue/dist/Components/ProgressBar'

export default {
	name: 'Backup',
	
	components: {
		Multiselect, 
		ActionButton, 
		EmptyContent,
		Modal,
		ProgressBar,
	},

	data() {
		return {
			loading: true,
			selectedBackup: false,
			backupData: [],
			interval: false,
			overlay: {
				active: false,
				title: '',
				text: '',
				mode: '',
				error: false,
				progress: 0,
				progressStep: '',
				canClose: true,
				enableSwipe: false,
			},
		}
	},
	computed: {
		lastBackup() {
			return this.backupData && this.backupData.last_backup
		},

		backups() {
			return (!this.backupData) 
				? [] 
				: this.backupData.found.map((item) => {
					const myDate = new Date(item.created * 1e3).toLocaleString()
					return {
						label: `${item.name} | created: ${myDate} | size: ${item.size}B`,
						id: item.created,
					}
				})
		},
	},
	async beforeMount() {
		await this.refresh()
		this.loading = false
	},

	methods: {
		async refresh() {
			const url = '/apps/nextbox/forward/backup'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.backupData = res.data.data
		},

		async start_backup() {
			this.overlay = {
				title: 'Running Full System Backup',
				active: true,
				mode: 'backup',
				canClose: false,
				error: false,
				progress: 0,
				text: 'Please wait, the backup operation is running...',
			}

			const url = '/apps/nextbox/forward/backup/start'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		
			this.interval = window.setInterval(this.update_progress, 1000)
		},
		
		async update_progress() {
			const res = await axios.get(`http://${document.location.host}:18585/overview`).catch((e) => {
				showError('Connection failed')
				console.error(e)
				this.overlay.canClose = true
				window.clearInterval(this.interval)
			})
			const data = res.data.data
			
			// something is wrong
			if (data.backup.unable) {
				window.clearInterval(this.interval)
				this.overlay.error = true
				this.overlay.canClose = true
				this.overlay.text = `The operation failed during step: ${data.backup.unable}`
				this.overlay.progressStep = 'Operation canceled due to error!'
				return
			}
			// regular operation mode
			if (data.backup.running) {
				const step = (data.backup.step === undefined) ? 'init' : data.backup.step
				switch (step) {
				case 'init':
					this.overlay.progressStep = 'Initializing...'
					break
				case 'apps':
					this.overlay.progressStep = 'Copying: Applications'
					break
				case 'db':
					this.overlay.progressStep = 'Copying: Database'
					break
				case 'data':
					this.overlay.progressStep = 'Copying: User Data'
					break
				}
				if (data.backup.progress) {
					this.overlay.progress = Math.round(data.backup.progress)
				}
			// once regular mode is finished...
			} else if (!data.backup.unable) {
				window.clearInterval(this.interval)
				this.overlay.progressStep = 'Finished successfully!'
				this.overlay.canClose = true
				this.overlay.text = ''
			}
		},

		async start_restore() {

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

.modal-box {
	width: 50vw;
	text-align: center;
	padding: 5vh;
}

</style>
