<template>
	<div id="backup-restore">
		<div v-if="progress" class="section">
			<h2>{{ progressWhat }} in Progress</h2>
			<br>

			<span v-if="progress.state === 'completed'" class="tag success"><span class="icon icon-checkmark" />
				Completed {{ progressWhat }} successfully
			</span>
			<span v-else-if="progress.state === 'failed'" class="tag error"><span class="icon icon-error" />
				Failed {{ progressWhat }} operation during {{ progress.who }}
			</span>
			<span v-else class="tag neutral"><span class="icon icon-loading-small" />
				{{ progressWhat }} - 
				Current State: <span class="bold">{{ progress.state }}</span> 
				Component: <span class="bold">{{ progress.who }}</span>
				Percent Done: <span class="bold">{{ progress.percent }}%</span>
			</span>
			<br>
			<br>
			
			<button type="button" :disabled="!['completed','failed'].includes(progress.state)" @click="clear_status()">
				<span class="icon icon-confirm" />
				Continue...
			</button>

		</div>

		<div v-if="!progress" class="section">
			<h2>Full System Backup</h2>
			You can create a new backup of your NextBox, or incrementally
			update an already existing backup.<br>

			<span v-if="lastBackup" class="tag success"><span class="icon icon-checkmark" />Your last backup was done at: <span class="bold">{{ new Date(lastBackup * 1e3).toLocaleString() }}</span></span>
			<span v-else class="tag warning"><span class="icon icon-close" />You have not yet run a backup - please do so</span><br>
			
			First select a device on which the backup should reside. You can
			only select devices mounted inside Storage Management:<br>
			<Multiselect 
				v-model="selectedDevice"
				:options="devices"
				:disabled="!Boolean(devices)"
				placeholder="Select Backup Device"
				track-by="path" 
				label="friendly_name" /><br><br>

			On the selected device you can select an existing backup:
			<Multiselect 
				v-model="selectedBackup"
				:options="device_backups(selectedDevice)"
				:disabled="!Boolean(selectedDevice)"
				@update="validateBackupLocation"
				placeholder="Select Backup Location"
				track-by="path" 
				label="name" /><br>
			Alternatively, create a new backup:<br>
			<input 
				v-model="newBackup" 
				type="text" 
				:disabled="selectedBackup || !selectedDevice" 
				@change="validateBackupLocation"
				placeholder="Name of new backup"><br>
			<span v-if="userMessage.newBackup" class="error-txt">{{ userMessage.newBackup.join(" ") }}</span><br>
			<br>

			<button type="button" :disabled="backupDisabled" @click="start_backup()">
				<span class="icon icon-download" />
				Start Backup now
			</button>
		</div>

		<div v-if="!progress" class="section">
			<h2>Restore System from Backup</h2>
			Select a Backup to restore the System from this Backup. Any existing 
			data will be replaced with the backup data!<br>
			<Multiselect 
				v-model="selectedRestore"
				:options="allBackups()"
				placeholder="Select Backup to Restore"
				track-by="path" 
				label="friendly_name" /><br><br><br>
			<button type="button" :disabled="restoreDisabled" @click="start_restore()">
				<span class="icon icon-upload" />
				Start Restoring now
			</button>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
// import { showError, showMessage, showSuccess, TOAST_PERMANENT_TIMEOUT } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

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
			interval: null,
			lastBackup: false,

			progress: false,
			backupLocation: '',

			selectedDevice: false,
			selectedBackup: false,
			newBackup: '',
			selectedRestore: false,
			
			devices: [],
			backups: {},

			// user messaging
			userMessage: {
				newBackup: [],
			},

		}
	},
	computed: {
		backupDisabled() {
			return !this.validateBackupLocation()
		},

		restoreDisabled() {
			return !this.selectedRestore
		},

		progressWhat() {
			return (this.progress.what === 'export') ? 'Backup' : 'Restore'
		},
	},

	async beforeMount() {
		await this.refresh()
		await this.update_progress()
		this.loading = false
	},

	methods: {
		async refresh() {
			const url = '/apps/nextbox/forward/backup'
			await axios.get(generateUrl(url)).then((res) => {
				this.devices = res.data.data.devices
				this.backups = res.data.data.backups
				this.lastBackup = res.data.data.last_backup
				this.selectedBackup = false
				this.selectedDevice = false
				this.newBackup = ''
				this.selectedRestore = false
			}).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		},

		async clear_status() {
			const url = '/apps/nextbox/forward/backup/status/clear'
			await axios.get(generateUrl(url)).then((res) => {
			
			}).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.progress = null
			this.refresh()
			if (this.interval) {
				window.clearInterval(this.interval)
			}
		},

		device_backups(dev) {
			if (!dev) {
				return []
			}
			return this.backups[dev.path]
		},

		allBackups() {
			const out = []
			for (const dev in this.devices) {
				const devPath = this.devices[dev].path
				for (const backup of this.backups[devPath]) {
					backup.friendly_name = `${backup.name} [${this.devices[dev].friendly_name}]`
					out.push(backup)
				}
			}
			return out
		},

		validateBackupLocation() {
			if (!this.selectedDevice) {
				this.userMessage.newBackup = []
				this.backupLocation = ''
				return false
			}

			if (Boolean(this.selectedBackup) && Boolean(this.selectedDevice)) {
				this.userMessage.newBackup = []
				this.newBackup = ''
				this.backupLocation = this.selectedBackup.path
				return true
			}

			if (this.newBackup === '' && Boolean(this.selectedDevice)) {
				this.userMessage.newBackup = [
					'Please select a location or enter a new backup location'
				]
				this.backupLocation = ''
				return false
			}

			const pat = /^[a-zA-Z0-9_]+$/
			if (!pat.test(this.newBackup)) {
				this.userMessage.newBackup = [
					'Invalid new backup location - use only alphanumeric letters and underscores.'
				]
				this.backupLocation = ''
				return false
			}
			if (this.newBackup.length < 4) {
				this.userMessage.newBackup = [
					'Invalid new backup location - at least 4 characters length required.'
				]
				this.backupLocation = ''
				return false
			}
			this.userMessage.newBackup = []
			this.backupLocation = this.selectedDevice.path + '/' + this.newBackup
			return true
		},

		async start_backup() {
			const url = '/apps/nextbox/forward/backup/start'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const data = qs.stringify({
				tar_path: this.backupLocation
			})

			const res = await axios.post(generateUrl(url), data, options).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		
			this.interval = window.setInterval(this.update_progress, 1000)
			await this.update_progress()
		},
		
		async update_progress() {
			const url = '/apps/nextbox/forward/backup/status'
			await axios.get(generateUrl(url)).then((res) => {
				this.progress = res.data.data
				// no progress to update => clear auto-update
				if (this.progress === null && this.interval) {
					window.clearInterval(this.interval)
				}
				// progress completed => clear auto-update
				if (this.progress !== null && this.progress.state === 'completed' && this.interval) {
					window.clearInterval(this.interval)
				}
			}).catch((e) => {
				//showError('Connection failed')
				//console.error(e)
			})
		},

		async start_restore() {
			const url = '/apps/nextbox/forward/backup/restore'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			const data = qs.stringify({
				src_path: this.selectedRestore.path
			})

			const res = await axios.post(generateUrl(url), data, options).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		
			this.interval = window.setInterval(this.update_progress, 1000)
			await this.update_progress()
		},
	},
}
</script>


<style scoped>

#backup-restore {
	display: flex;
	width: 100%;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}


.modal-box {
	width: 50vw;
	text-align: center;
	padding: 5vh;
}

.multiselect {
	width: 90%;
	min-height: 36px;
}


</style>
