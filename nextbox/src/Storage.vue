<template>
	<div class="storage">
		<AppContentList class="section storage-list" show-details>
			<h2>Mounted Storages</h2>

			<ListItemIcon v-for="dev in mountedDevs" 
				:key="dev"
				class="list-item"
				:title="getListName(dev)"
				:subtitle="getListDesc(dev)"
				display-name="icon-add"
				:icon-class="(loading === dev) ? 'icon-loading-small' : 'icon-add'"
				:avatar-size="36">
				<Actions>
					<ActionButton v-for="menuitem in getActions(dev)"
						:key="menuitem.name"
						:close-after-click="true"
						:icon="menuitem.icon" 
						@click="action(dev, menuitem)">
						{{ menuitem.name }}
					</ActionButton>
				</Actions>
			</ListItemIcon>
		</AppContentList>

		<AppContentList class="section storage-list" show-details>
			<h2>Available Storages</h2>
			<ListItemIcon v-for="dev in availableDevs" 
				:key="dev"
				class="list-item"
				:title="getListName(dev)"
				:subtitle="getListDesc(dev)"
				display-name="icon-add"
				:icon-class="(loading === dev) ? 'icon-loading-small' : 'icon-add'"
				:avatar-size="36">
				<Actions>
					<ActionButton v-for="menuitem in getActions(dev)"
						:key="menuitem.name"
						:close-after-click="true"
						:icon="menuitem.icon" 
						@click="action(dev, menuitem)">
						{{ menuitem.name }}
					</ActionButton>
				</Actions>
			</ListItemIcon>
			<EmptyContent v-if="!available" icon="icon-close">
				No Unmounted Available
			</EmptyContent>
		</AppContentList>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'
import Actions from '@nextcloud/vue/dist/Components/Actions'
import ActionButton from '@nextcloud/vue/dist/Components/ActionButton'
import EmptyContent from '@nextcloud/vue/dist/Components/EmptyContent'

export default {
	name: 'Storage',

	components: {
		AppContentList, 
		ListItemIcon, 
		Actions, 
		ActionButton, 
		EmptyContent,
	},

	/*props: { 
		isMounted: { type: Boolean },
		title: { type: String, default: () => '' },
		data: { type: Object, default: () => {} },
	},*/

	data() {
		return {
			loading: true,
			msg: '',
			storages: {},
		}
	},
	computed: {
		mountedDevs() {
			return ('mounted' in this.storages) ? Object.keys(this.storages.mounted) : []
		},
		availableDevs() {
			return ('available' in this.storages) 
				? this.storages.available.filter((x) => !(x in this.storages.mounted)) 
				: []
		},
		mounted() {
			return this.storages.mounted 
		},

		available() {
			return this.storages.available
		},
	},

	async mounted() {
		this.loading = true
		await this.refreshStorage()
		this.loading = false
	},

	methods: {
		getListName(dev) {
			const blockDev = dev.split('/').slice(-1)[0].slice(0, 3)
			const desc = this.storages.block_devs[blockDev].name
			if (!this.mountedDevs.includes(dev)) {
				return desc
			}
			if (this.storages.main === dev) {
				return `Main (${desc})`
			} else if (this.storages.backup === dev) {
				return `Backup (${desc})`
			}
			return `Extra (${desc})`
		},

		getListDesc(dev) {
			const two = (this.mounted[dev]) ? this.mounted[dev] + ` (${this.storages.type[dev]})` : '(not mounted)'
			return `${dev} @ ${two}`
		},

		getActions(dev) {
			const devFn = dev.split('/').slice(-1)[0]
			const UmountTarget = dev in this.mounted ? this.mounted[dev].split('/').slice(-1)[0] : ''
			if (this.storages.main !== dev) {
				if (this.mountedDevs.includes(dev)) {
					if (this.storages.backup !== dev) {
						return [{ icon: 'icon-close', name: 'Unmount Partition', target: UmountTarget, act: 'umount' }]
					}
				} else {
					return [{ icon: 'icon-add', name: 'Mount as Extra Storage', target: devFn, act: 'mount-extra' }]
				}
			}
		},

		async refreshStorage() {
			const res = await axios
				.get(generateUrl('/apps/nextbox/forward/storage'))
				.catch((e) => {
					showError('Could not load Storage data')
					console.error(e)
				})
			this.storages = res.data.data
		},

		async action(dev, obj) {
			this.loading = dev

			
			let url = ''
			if (obj.act === 'mount-backup') {
				url = `/apps/nextbox/forward/storage/mount/${obj.target}/backup`
			} else if (obj.act === 'mount-extra') {
				url = `/apps/nextbox/forward/storage/mount/${obj.target}`
			} else if (obj.act === 'umount') {
				url = `/apps/nextbox/forward/storage/umount/${obj.target}`
			}

			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			
			showMessage(res.data.msg)
			this.refreshStorage()
			this.loading = false
		},
	},
}
</script>


<style scoped>
.storage-list { 
	display: flex;
	width: 100%;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	/*height: fit-content !important;*/
}

.storage {
	/*height: 45vh;*/
}

.empty {
	height: 0px;
	margin: 0;
	padding: 0;
}

.list-item:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}

.avatar-class-icon {
	background-color: none !important;
}

</style>
