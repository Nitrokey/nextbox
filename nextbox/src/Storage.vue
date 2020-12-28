<template>
	<div>
		<AppContentList show-details>
			<ListItemIcon v-for="item in items"
				:key="item.two"
				:title="item.one"
				:subtitle="item.two"
				:icon="item.icon" />
		</AppContentList>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'

export default {
	name: 'Storage',
	components: {
		AppContentList, ListItemIcon
	},
	props: { isMounted: Boolean },

	data() {
		return {
			loading: true,
			items: [],
		}
	},

	async mounted() {
		try {
			const res = await axios.get(generateUrl('/apps/nextbox/forward/storage'))
			const data = res.data.data
			const mounted = data.mounted
			const mountedDevs = Object.keys(data.mounted)

			this.items = data.available
				.filter(dev => (!(this.isMounted ^ mountedDevs.includes(dev))))
				.map(dev => {
					const blockDev = dev.split('/').slice(-1)[0].slice(0, 3)
					const desc = data.block_devs[blockDev].name
					const two = (mounted[dev]) ? mounted[dev] + ` (${data.type[dev]})` : '(not mounted)'
					const ret = {
						icon: 'HD',
						two,
						details: dev
					}

					ret.bg = 'rgb(100, 155, 155)'
					if (!this.isMounted && mountedDevs.includes(dev)) {
						ret.bg = 'rgb(220, 220, 220)'
					}

					ret.one = desc
					if (mountedDevs.includes(dev)) {
						ret.one = `Extra (${desc})`
						if (data.main === dev) {
							ret.one = `Main (${desc})`
						} else if (data.backup === dev) {
							ret.one = `Backup (${desc})`
						}
					}

					if (data.main !== dev) {
						if (mountedDevs.includes(dev)) {
							ret.menu = [
								{ icon: 'close', name: 'Unmount Partition', cls: 'storage-umount' }
							]
						} else {

							ret.menu = [{ icon: 'add', name: 'Mount as Extra Storage', cls: 'storage-extra-mount' }]
							if (data.backup === null) {
								ret.menu.push({ icon: 'folder', name: 'Mount as Backup Storage', cls: 'storage-backup-mount' })
							}

							//ret.menu.push({icon: 'folder', input_value: '[mount-name]'})
						}
					}
					return ret
				})

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
.logline { color: black }
</style>
