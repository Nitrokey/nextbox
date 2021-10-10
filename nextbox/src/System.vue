7<template>
	<div id="system" v-if="!loading">
		<div class="section">
			<h2>System Logs</h2>
			Downloading the system logs will allow you an extensive view into the state of your system.<br>
			<button type="button" @click="get_logs()">
				<span class="icon icon-confirm" />
				Download System Logs
			</button>
		</div>

		<div class="section">
			<h2>NextBox Token</h2>
			Your personal <span class="bold">NextBox Quickstart Token</span>:<br>
			<input v-model="update.nk_token" type="text" disabled="true">
			<br><span v-if="userMessage.nk_token" class="error-txt">{{ userMessage.nk_token.join(" ") }}</span><br>
		</div>

		<div class="section">
			<h2>SSH Access Control</h2>
			
			<div v-if="pubkey">
				Your NextBox is configured to grant access through SSH. <br>
				To connect to your NextBox, use your local IP: <b>{{ this.local_ip }}</b> 
				(on default port 22) and the user: <b>nextuser</b><br>
				No password is required, the provided public-key together with
				your private-key is used for 
				{{ toLink('en.wikipedia.org/wiki/Key_authentication', 'key-based authentication') }}.<br>
				The user has passwordless sudo pre-configured for unrestricted root access.<br>
				Please be aware that Nitrokey cannot give you support for changes done using the SSH
				access, use it at your own risk!
			</div><div v-else>
				Currently SSH access is deactivated! To get access to your NextBox via SSH, 
				please provide a public key suitable for SSH's <b>authorized_keys</b> file.<br>
				<input v-model="update.pubkey" 
					type="text" 
					placeholder="Public Key: <algorithm> <public-key-data> <user>@<host>">
			</div>

			<button v-if="!pubkey" type="button" @click="toggle_ssh('on')">
				<span class="icon icon-confirm" />
				Activate SSH Access
			</button>
			<button v-else type="button" @click="toggle_ssh('off')">
				<span class="icon icon-close" />
				Deactivate SSH Access
			</button>
		</div>

		<div class="section">
			<h2>System Power State</h2>
			<div>
				There usually is no need to reboot the NextBox. But especially,
				if you plan to transport the NextBox, powering it off before, is 
				recommended.
			</div>

			<button type="button" @click="powerop('reboot')">
				<span class="icon icon-history" />
				Reboot
			</button>
			<button type="button" @click="powerop('poweroff')">
				<span class="icon icon-close" />
				Poweroff
			</button>
		</div>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
// import { showError, showSuccess } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

import toLink from './utils.js'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'

const FileDownload = require('js-file-download')

export default {
	name: 'System',

	components: {
	},

	data() {
		return {
			loading: true,
			
			// update-ables
			update: {
				pubkey: '',
				nk_token: '',
			},
			
			// user messaging
			userMessage: {
				nk_token: [],
			},

			// constants (after refresh)
			pubkey: '',
			local_ip: '',
			config: {},
		}
	},

	async mounted() {
		this.refresh()
		this.loading = false
	},

	methods: {
		toLink,

		async refresh() {
			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/ssh'))
				this.update.pubkey = res.data.data.pubkey.trim()
				this.pubkey = res.data.data.pubkey.trim()
				this.local_ip = res.data.data.local_ip

			} catch (e) {
				console.error(e)
			}

			const url = '/apps/nextbox/forward/config'
			const res = await axios.get(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.config = res.data.data
			this.update.nk_token = res.data.data.nk_token
		},
		
		async powerop(op) {
			let url = ''
			if (op === 'poweroff') {
				url = '/apps/nextbox/forward/poweroff' 
			} else if (op === 'reboot') {
				url = '/apps/nextbox/forward/reboot'
			}
			const res = await axios.post(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})

				
		},

		check_token() {
			if (this.update.nk_token === null || this.update.nk_token.length !== 36) {
				this.userMessage.nk_token = ['Please insert a valid token']
				return false
			}

			this.userMessage.nk_token = []
			return true
		},

		async get_logs() {
			axios({
				url: generateUrl('/apps/nextbox/forward/logs'),
				//responseType: 'blob',
			}).then((res) => {
				const decodedData = atob(res.data.data.zip)
				const uInt8Array = new Uint8Array(decodedData.length)

				for (let i = 0; i < decodedData.length; ++i) {
					uInt8Array[i] = decodedData.charCodeAt(i)
				}

				return FileDownload(new Blob([uInt8Array], { type: 'application/zip' }), 'nextbox-logs.zip')
			})
		},


		async toggle_ssh(what) {
			const url = '/apps/nextbox/forward/ssh'
			const options = {
				headers: { 'content-type': 'application/x-www-form-urlencoded' },
			}
			try {
				const data = qs.stringify((what === 'on') 
					? { pubkey: this.update.pubkey }
					: { pubkey: '' })

				const res = await axios.post(generateUrl(url), data, options)
				this.refresh()
				return res.data.result === 'success'

			} catch (e) {
				showError('Connection failed')
				console.error(e)
				return false
			}
		},
	},
}
</script>


<style scoped>

#system {
	display: flex;
	min-width: 0px;
	min-height: 0px;
	max-width: none;
	height: fit-content !important;
}

.section {
	display: block;
	padding: 30px;
	margin: 0;
	height: fit-content !important;
}

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}


.txt {
	width: 25vw;
}


</style>
