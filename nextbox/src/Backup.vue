<template>
	<div class="backup-restore">
		<div class="section">
			<h2>Choose Backup Device</h2>
			Select the device you would like to use for backups here. 
			<span class="bold">Please note that a device can only be mounted either for backups or for extra storage</span>
			<br>
			<Multiselect 
				v-model="selectedDevice"
				:options="devices"
				:disabled="storages.backup"
				track-by="id" 
				label="label" />
			<br>
			<button type="button" :disabled="selectedDevice === false" @click="deviceAction()">
				<span class="icon icon-confirm" />
				{{ (storages.backup) ? "Unmount Backup Drive" : "Mount as Backup Drive" }}
			</button>
		</div>

		<div class="section">
			<h2>Full System Backup</h2>
			You can start a full backup here. Nextcloud will change into maintainance mode 
			and will not be available during the backup operation. Once the backup is started 
			you will see a progress indicator, if you reload you won't be able to see the 
			progress until the operation finished.<br>
			<!-- ActionButton
				icon="icon-download" 
				@click="start_backup()">
				Start Backup now
			</ActionButton -->
			<span v-if="lastBackup" class="tag success"><span class="icon icon-checkmark" />Your last backup was done at: <span class="bold">{{ new Date(lastBackup * 1e3).toLocaleString() }}</span></span>
			<span v-else class="tag warning"><span class="icon icon-close" />You have not yet run a backup - please do so</span>
			<br>
			<button type="button" :disabled="!storages.backup" @click="start_backup()">
				<span class="icon icon-download" />
				Start Backup now
			</button>
		</div>

		<div class="section">
			<h2>Restore System from Backup</h2>
			<div v-if="lastBackup">
				Similar to the backup process, restoring the system from a 
				backup will set Nextcloud into maintainance mode and you 
				will be presented with a progress indicator.<br>
				<br>
				<Multiselect 
					v-model="selectedBackup"
					:options="backups"
					track-by="id" 
					label="label" />
				<!-- ActionButton
					:disabled="selectedBackup === false"
					icon="icon-upload" 
					@click="start_restore(selectedBackup)">
					Start Restoring now
				</ActionButton -->
				<button type="button" :disabled="selectedBackup === false" @click="start_restore(selectedBackup)">
					<span class="icon icon-upload" />
					Start Restoring now
				</button>
			</div>
			<EmptyContent v-if="!lastBackup" icon="icon-close">
				No Backup to restore available yet...
			</EmptyContent>
		</div>

		<Modal 
			v-if="overlay.active"
			v-model="overlay"
			dark
			@close="close_modal($event)">
			<div class="modal-box">
				<span class="bold">{{ overlay.text }}</span><br><br>
				<ProgressBar 
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
import { showError, showMessage, showSuccess, TOAST_PERMANENT_TIMEOUT } from '@nextcloud/dialogs'
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
			
			selectedDevice: false,
			storages: {},

			interval: false,
			overlay: {
				active: false,
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
						id: item.name,
					}
				})
		},

		devices() {
			if (!('available' in this.storages)) return []
			
			return this.storages.available
				.filter((dev) => !(dev in this.storages.mounted))
				.map((dev) => {
					return {
						label: this.getDevLabel(dev),
						id: dev,
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
			await axios.get(generateUrl(url)).then((res) => {
				this.backupData = res.data.data
			}).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			
			await axios.get(generateUrl('/apps/nextbox/forward/storage'))
				.then((res) => {
					this.storages = res.data.data
					if (this.storages.backup) {
						this.selectedDevice = {
							label: this.getDevLabel(this.storages.backup),
							id: this.storages.backup,
						}
					}
				}).catch((e) => {
					showError('Could not load Storage data')
					console.error(e)
				})
		},

		getDevLabel(dev) {
			const blockDev = dev.split('/').slice(-1)[0].slice(0, 3)
			const desc = this.storages.block_devs[blockDev].name
			return `${desc} | ${dev}`
		},

		async deviceAction() {
			const dev = (this.storages.backup) ? this.storages.backup : this.selectedDevice.id
			const devFn = dev.split('/').slice(-1)[0]
			const UmountTarget = dev in this.storages.mounted 
				? this.storages.mounted[dev].split('/').slice(-1)[0] 
				: ''

			const url = (!this.storages.backup)
				? `/apps/nextbox/forward/storage/mount/${devFn}/backup`
				: `/apps/nextbox/forward/storage/umount/${UmountTarget}`
			
			axios.get(generateUrl(url)).then((res) => {
				const what = (this.storages.backup) ? 'Unmounting' : 'Mounting'
				if (res.data.result === 'success') {
					showSuccess(`${what} completed`)
					this.refresh()
				} else {
					showError(`${what} failed`)
				}

			}).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		},

		async close_modal(ev) {
			this.overlay.active = false
		},

		async start_backup() {
			this.overlay = { 
				...this.overlay, 
				...{
					active: true,
					canClose: false,
					error: false,
					progress: 0,
					text: 'Please wait, the backup operation is running...',
					progressStep: 'Preparing....',
				},
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

			// fail getting overview
			if (!('data' in res.data)) {
				return
			}

			const data = res.data.data
			
			// something is wrong
			if (data.backup.unable) {
				window.clearInterval(this.interval)
				this.overlay = { 
					...this.overlay, 
					...{
						error: true,
						canClose: true,
						text: `The operation failed during step: ${data.backup.unable}`,
						progressStep: 'Operation canceled due to error!',
					},
				}
				return
			}

			// regular operation mode
			if (data.backup.running) {
				const step = (data.backup.step === undefined) ? 'init' : data.backup.step
				let percent = '   0%'
				if (data.backup.progress) {
					this.overlay.progress = Math.round(data.backup.progress)
					percent = `${this.overlay.progress}%`.padStart(5)
				}
				
				switch (step) {
				case 'init':
					this.overlay.progressStep = 'Initializing...'
					break
				case 'apps':
					this.overlay.progressStep = `Copying: Applications ${percent}`
					break
				case 'db':
					this.overlay.progressStep = `Copying: Database ${percent}`
					break
				case 'data':
					this.overlay.progressStep = `Copying: User Data ${percent}`
					break
				}
				
			// once regular mode is finished...
			} else if (!data.backup.unable) {
				window.clearInterval(this.interval)
				this.overlay = { 
					...this.overlay, 
					...{
						progressStep: '',
						canClose: true,
						text: 'Finished successfully!',
					},
				}
				this.refresh()
			}
		},

		async start_restore(which) {
			this.overlay = { 
				...this.overlay, 
				...{
					active: true,
					canClose: false,
					error: false,
					progress: 0,
					text: 'Please wait, the restore operation is running...',
					progressStep: 'Preparing....',
				},
			}

			const url = `/apps/nextbox/forward/backup/restore/${which.id}`
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
		
			this.interval = window.setInterval(this.update_progress, 1000)
			this.selectedBackup = false
		},
	},
}
</script>


<style scoped>

.backup-restore {
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
