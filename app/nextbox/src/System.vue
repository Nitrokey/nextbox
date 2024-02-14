<template>
	<div id="system" v-if="!loading">
		<div class="section">
			<h2>System Logs</h2>
			Downloading the system logs will allow you an extensive view into the state of your system.<br>
			<button type="button" :disabled="logsDisabled" @click="getLogs()">
				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-close')" />
				Download System Logs
			</button>
		</div>

		<div class="section">
			<h2>NextBox Token</h2>
			Your personal <b>NextBox Quickstart Token</b>:<br>
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
				<span v-html="toLink('en.wikipedia.org/wiki/Key_authentication', 'key-based authentication')" />.<br>
				The user has passwordless sudo pre-configured for unrestricted root access.
			</div><div v-else>
				Currently SSH access is deactivated! To get access to your NextBox via SSH, 
				please provide a public key suitable for SSH's <b>authorized_keys</b> file.<br>
				<input v-model="update.pubkey" 
					type="text" 
					placeholder="<algorithm> <public-key-data> <user>@<host> (ssh format public key)">
				<br><span v-if="userMessage.pubkey" class="error-txt">{{ userMessage.pubkey.join(" ") }}</span><br>
			
			</div>
			<button v-if="!pubkey" 
				type="button" 
				:disabled="sshDisabled" 
				@click="toggleSSH('on')">

				<span :class="'icon ' + ((loadingButton) ? 'icon-loading-small' : 'icon-confirm')" />
				Activate SSH Access
			</button>
			<button v-else type="button" @click="toggleSSH('off')">
				<span class="icon icon-close" />
				Deactivate SSH Access
			</button>
			<div v-if="pubkey">
				Please be aware that Nitrokey cannot give you support for changes done using the SSH
				access, use it at your own risk!
			</div>
		</div>

                
		<div class="section" v-if="canDebianUpdate">
			<h2>System Debian Update</h2>
			<div>
				Here you can trigger the system update script manually. Updating to the newest Debian Version might be mandatory in the future to receive any updates or support. <br>
				WARNING! <br>
				Beware that this may cause problems and may break your system! Please back up any data you don't want to loose! <br>
				Don't turn off your device until the status LED is green (not blinking!), this may take around an hour or two. Turning it off will break your system! <br>
				You will need to confirm by pressing the button twice.
			</div>

			<button type="button" @click="updateDebian" ref="btnUpdateDebian">
				<span class="icon icon-history" />
				Update
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

import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'
import qs from 'qs'

import UtilsMixin from './UtilsMixin.js'


// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'
// import AppContentDetails from '@nextcloud/vue/dist/Components/AppContentDetails'

const FileDownload = require('js-file-download')
let updateButtonPressed = false



export default {
	name: 'System',
	mixins: [UtilsMixin],

	components: {
	},

	data() {
		return {
			loading: true,
			loadingButton: true,
			canDebianUpdate: false,
			
			// update-ables
			update: {
				pubkey: '',
				nk_token: '',
			},
			
			// user messaging
			userMessage: {
				nk_token: [],
				pubkey: [],
			},

			// constants (after refresh)
			pubkey: '',
			local_ip: '',
			config: {},
		}
	},

	
	computed: {
		sshDisabled() {
			return this.loadingButton || !this.checkPubkey()
		},

		logsDisabled() {
			return this.loadingButton
		},
	},
	
	mounted() {
		this.refresh()
		this.loading = false
		this.loadingButton = false
	},

	methods: {
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

			try {
				const res = await axios.get(generateUrl('/apps/nextbox/forward/debianVersion'))
				this.canDebianUpdate = (res.data.data.version === 10)
			} catch (e) {
				console.error(e)
			}
		},


		updateDebian() {
			this.loadingButton = true
			if (!updateButtonPressed) {
				updateButtonPressed = true
				this.$refs.btnUpdateDebian.innerText = 'Confirm Update (Please read warnings above!)'
			} else {
				let url = ''
				url = '/apps/nextbox/forward/updateDebian'
				const res = axios.post(generateUrl(url)).catch((e) => {
					showError('Connection failed')
					console.error(e)
				})
			}
			this.loadingButton = false
		},

		powerop(op) {
			this.loadingButton = true
			let url = ''
			if (op === 'poweroff') {
				url = '/apps/nextbox/forward/poweroff' 
			} else if (op === 'reboot') {
				url = '/apps/nextbox/forward/reboot'
			}
			const res = axios.post(generateUrl(url)).catch((e) => {
				showError('Connection failed')
				console.error(e)
			})
			this.loadingButton = false
		},

		checkToken() {
			if (this.update.nk_token === null || this.update.nk_token.length !== 36) {
				this.userMessage.nk_token = ['Please insert a valid token']
				return false
			}

			this.userMessage.nk_token = []
			return true
		},

		checkPubkey() {
			if (!this.update.pubkey) {
				this.userMessage.pubkey = []
				return false
			} 

			const key = (this.update.pubkey || '').trim()
			const pubToks = key.split(' ')
			
			// if we re-assign too early, we'll never get 3 whitespaces :D
			if (pubToks.length === 3) {
				this.update.pubkey = key
			}

			if (pubToks.length !== 3) {
				this.userMessage.pubkey = ['The public key must consist of 3 compontents: '
								         + 'algorithm, key-data and user with host']
				return false
			}

			if (pubToks.some((tok) => tok.length < 3)) {
				this.userMessage.pubkey = ['Each component has a minimal length of 3']
				return false
			}

			if (!pubToks.slice(-1)[0].includes('@')) {
				this.userMessage.pubkey = ['The last component needs to be in <user>@<hostname> format']
				return false
			}
			this.userMessage.pubkey = []
			return true
		},

		getLogs() {
			this.loadingButton = true
			axios({
				url: generateUrl('/apps/nextbox/forward/logs'),
				//responseType: 'blob',
			}).then((res) => {
				const decodedData = atob(res.data.data.zip)
				const uInt8Array = new Uint8Array(decodedData.length)

				for (let i = 0; i < decodedData.length; ++i) {
					uInt8Array[i] = decodedData.charCodeAt(i)
				}

				this.loadingButton = false
				return FileDownload(new Blob([uInt8Array], { type: 'application/zip' }), 'nextbox-logs.zip')
				
			})
			
		},


		async toggleSSH(what) {
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
