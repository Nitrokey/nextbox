<template>
	<AppContentList class="storage-list" show-details>
		<h2>
			{{ title }}
		</h2>

		<ListItemIcon v-for="item in items"
			:key="item.two"
			:title="item.one"
			:subtitle="item.two"
			:display-name="item.icon"
			:icon-class="icon-add"
			:avatar-size="36">
			<Actions>
				<ActionButton v-for="menuitem in item.menu"
					:key="menuitem.name"
					:close-after-click="true"
					:icon="menuitem.icon" 
					@click="action(menuitem)">
					{{ menuitem.name }}
				</ActionButton>
			</Actions>
		</ListItemIcon>
	</AppContentList>
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

export default {
	name: 'Storage',

	components: {
		AppContentList, ListItemIcon, Actions, ActionButton,
	},

	props: { 
		isMounted: Boolean,
		title: String,
		data: Object
	},

	data() {
		return {
			loading: true,
			msg: '',
		}
	},
	computed: {
		mountedDevs() {
			return Object.keys(this.data.mounted)
		},

		mounted() {
			return this.data.mounted
		},

		items() { 
			if (!this.data.available) {
				return []
			}

			return this.data.available
				.filter(dev => (!(this.isMounted ^ this.mountedDevs.includes(dev))))
				.map(dev => {
					const blockDev = dev.split('/').slice(-1)[0].slice(0, 3)
					const desc = this.data.block_devs[blockDev].name
					const two = (this.mounted[dev]) ? this.mounted[dev] + ` (${this.data.type[dev]})` : '(not mounted)'
					const ret = {
						icon: 'HD',
						two: `${dev} @ ${two}`,
					}

					ret.bg = 'rgb(100, 155, 155)'
					if (!this.isMounted && this.mountedDevs.includes(dev)) {
						ret.bg = 'rgb(220, 220, 220)'
					}

					ret.one = desc
					if (this.mountedDevs.includes(dev)) {
						ret.one = `Extra (${desc})`
						if (this.data.main === dev) {
							ret.one = `Main (${desc})`
						} else if (this.data.backup === dev) {
							ret.one = `Backup (${desc})`
						}
					}

					const devFn = dev.split('/').slice(-1)[0]
					const UmountTarget = dev in this.mounted ? this.mounted[dev].split('/').slice(-1)[0] : ''
					if (this.data.main !== dev) {
						if (this.mountedDevs.includes(dev)) {
							ret.menu = [
								{ icon: 'icon-close', name: 'Unmount Partition', target: UmountTarget, act: 'umount' },
							]
						} else {

							ret.menu = [{ icon: 'icon-add', name: 'Mount as Extra Storage', target: devFn, act: 'mount-extra' }]
							if (this.data.backup === null) {
								ret.menu.push({ icon: 'icon-folder', name: 'Mount as Backup Storage', target: devFn, act: 'mount-backup' })
							}
						}
					}
					return ret
				})
		},
	},

	async mounted() {
		this.loading = true
		this.$emit('refresh-storage')
		this.loading = false
	},

	methods: {
		async action(obj) {
			this.loading = true
			
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
			this.$emit('refresh-storage')
			this.loading = false
		},
	},
}
</script>


<style scoped>
.storage-list { 
	top: 65px !important; 
	display: flex;
	width: 100%;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
	
}
</style>
