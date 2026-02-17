<template>
	<div id="storage" v-if="!loading">
		<NcAppContentList class="section storage-list" show-details>
			<h2>Mounted Storages</h2>

			<NcListItemIcon v-for="dev in mountedDevs"
				:key="dev.name"
				class="list-item"
				:name="dev.friendly_name"
				:subname="getListDesc(dev)">
				<template #icon>
					<span :class="(loading === dev) ? 'icon-loading-small' : 'icon-add'" />
				</template>
				<template #actions>
					<NcActions>
						<NcActionButton v-for="menuitem in getActions(dev)"
							:key="menuitem.name"
							:close-after-click="true"
							@click="action(dev, menuitem)">
							<template #icon>
								<span :class="menuitem.icon" />
							</template>
							{{ menuitem.name }}
						</NcActionButton>
					</NcActions>
				</template>
			</NcListItemIcon>
		</NcAppContentList>

		<NcAppContentList class="section storage-list" show-details>
			<h2>Available Storages</h2>
			<NcListItemIcon v-for="dev in availableDevs"
				:key="dev.name"
				class="list-item"
				:name="dev.friendly_name"
				:subname="getListDesc(dev)">
				<template #icon>
					<span :class="(loading === dev) ? 'icon-loading-small' : 'icon-add'" />
				</template>
				<template #actions>
					<NcActions>
						<NcActionButton v-for="menuitem in getActions(dev)"
							:key="menuitem.name"
							:close-after-click="true"
							@click="action(dev, menuitem)">
							<template #icon>
								<span :class="menuitem.icon" />
							</template>
							{{ menuitem.name }}
						</NcActionButton>
					</NcActions>
				</template>
			</NcListItemIcon>
			<NcEmptyContent v-if="!availableDevs">
				<template #icon>
					<span class="icon-close" />
				</template>
				<template #name>
					No Unmounted Available
				</template>
			</NcEmptyContent>
		</NcAppContentList>
	</div>
</template>


<script>

import '@nextcloud/dialogs/style.css'
import { generateUrl } from '@nextcloud/router'
// import { showError, showMessage, showSuccess } from '@nextcloud/dialogs'
import { showError, showMessage } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import NcAppContentList from '@nextcloud/vue/components/NcAppContentList'
import NcListItemIcon from '@nextcloud/vue/components/NcListItemIcon'
import NcActions from '@nextcloud/vue/components/NcActions'
import NcActionButton from '@nextcloud/vue/components/NcActionButton'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'


import UtilsMixin from './UtilsMixin.js'

export default {
	name: 'Storage',
	mixins: [UtilsMixin],

	components: {
		NcAppContentList,
		NcListItemIcon,
		NcActions,
		NcActionButton,
		NcEmptyContent,
	},

	data() {
		return {
			loading: true,
			msg: '',
			storages: {},
		}
	},
	computed: {
		mountedDevs() {
			const ret = []
			for (const devName in this.storages) {
				const dev = this.storages[devName]
				for (const partName in dev.parts) {
					const part = dev.parts[partName]
					if (part.mounted) {
						ret.push(part)
					}
				}
			}
			return ret
		},
		availableDevs() {
			const ret = []
			for (const devName in this.storages) {
				const dev = this.storages[devName]
				for (const partName in dev.parts) {
					const part = dev.parts[partName]
					if (!part.mounted) {
						ret.push(part)
					}
				}
			}
			return ret
		},
	},

	async mounted() {
		await this.refreshStorage()
		this.loading = false
	},

	methods: {
		getListDesc(dev) {
			let space = ''
			if (dev.mounted) {
				const togb = 2 ** 30
				const free = Math.round((dev.space.free / togb) * 10) / 10
				const avail = Math.round((dev.space.avail / togb) * 10) / 10
				space = `Space: ${free}GB / ${avail}GB`
			}
			let fsinfo = '' 
			if (dev.mounted !== '/' && dev.mounted !== '/srv') {
				fsinfo = ` | (${dev.fs})`
				if (!['ext4', 'ext3', 'xfs', 'btrfs'].includes(dev.fs)) {
					fsinfo += ' Not available for backups (unsupported filesystem)'
				}
			}
			return (dev.mounted) ? `/dev/${dev.name} @ ${dev.mounted} | ${space}${fsinfo}` : `/dev/${dev.name}`
		},

		getActions(dev) {
			if (!dev.special) {
				// mount = "device name", umount = "mount point" as target
				const target = (dev.mounted) ? dev.mounted.split('/').splice(-1)[0] : dev.name
				if (dev.mounted) {
					return [{ icon: 'icon-close', name: 'Unmount Partition', target, act: 'umount' }]
				} else {
					return [{ icon: 'icon-add', name: 'Mount as Extra Storage', target, act: 'mount-extra' }]
				}
			}
			return []
		},

		async refreshStorage() {
			/*this->storages = [{
					<blockdev1> = { 
						<name>, 
						<model>, 
						<parts> = [{ 
							<part> = { <label>, <mounted>, <name>, <special>, <space>: {} }, ...
						}]
					}, ...
				}]
				*/
			const res = await axios
				.get(generateUrl('/apps/nextbox/forward/storage'))
				.catch((e) => {
					showError('Could not load storage data')
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

/*#storage {
	
}*/

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
