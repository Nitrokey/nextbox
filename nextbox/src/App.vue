<template>
	<div id="content" class="app-nextbox">
		<AppNavigation v-if="page !== 'backup_exclusive'">
			<ul>
				<AppNavigationItem :title="t('nextbox', 'Overview')" icon="icon-home" @click="set_page('overview')" />
				<AppNavigationItem :title="t('nextbox', 'Storage Management')" icon="icon-category-files" @click="set_page('storage')" />
				<AppNavigationItem :title="t('nextbox', 'Backup / Restore')" icon="icon-download" @click="set_page('backup')" />
				<AppNavigationItem :title="t('nextbox', 'Remote Access')"
					icon="icon-timezone"
					:allow-collapse="false"
					:open="isRemoteOpen"
					@click="set_page('remote')">
					<template>
						<AppNavigationItem :title="t('nextbox', 'Backwards Proxy')" icon="icon-star" @click="set_page('remote_proxy')" />
						<AppNavigationItem :title="t('nextbox', 'Guided Dynamic DNS')" icon="icon-comment" @click="set_page('remote_dyndns')" />
						<AppNavigationItem :title="t('nextbox', 'Custom Dynamic DNS')" icon="icon-settings" @click="set_page('remote_custom_dns')" />
						<AppNavigationItem :title="t('nextbox', 'Static Domain')" icon="icon-public" @click="set_page('remote_static_dns')" />
						<AppNavigationItem :title="t('nextbox', 'HTTPS / TLS')" icon="icon-password" @click="set_page('tls')" />
					</template>
				</AppNavigationItem>
				
				<AppNavigationItem :title="t('nextbox', 'System Settings')" icon="icon-settings" @click="set_page('system')" />
				<!-- AppNavigationItem :title="t('nextbox', 'Daemon Logs')" icon="icon-info" @click="set_page('logs')" /-->
			</ul>
		</AppNavigation>
			
		<AppContent>
			<Overview v-if="page === 'overview'" />
			<Storage v-if="page === 'storage'" />
			<Backup v-if="page === 'backup' || page === 'backup_exclusive'" @newPage="set_page" />
			<System v-if="page === 'system'" />
			<Logs v-if="page === 'logs'" />
			<Proxy v-if="page === 'remote_proxy'" @newPage="set_page" />
			<DynDNS v-if="page === 'remote_dyndns'" @newPage="set_page" />
			<CustomDNS v-if="page === 'remote_custom_dns'" @newPage="set_page" />
			<StaticDNS v-if="page === 'remote_static_dns'" @newPage="set_page" />
			<TLS v-if="page === 'tls'" @newPage="set_page" />
			<Remote v-if="page === 'remote'" @newPage="set_page" />
		</AppContent>
	</div>
</template>

<script>

import AppContent from '@nextcloud/vue/dist/Components/AppContent'
import AppNavigation from '@nextcloud/vue/dist/Components/AppNavigation'
import AppNavigationItem from '@nextcloud/vue/dist/Components/AppNavigationItem'

// import AppContentList from '@nextcloud/vue/dist/Components/AppContentList'
// import ListItemIcon from '@nextcloud/vue/dist/Components/ListItemIcon'

import Logs from './Logs'
import System from './System'
import DynDNS from './DynDNS'
import StaticDNS from './StaticDNS'
import CustomDNS from './CustomDNS'
import Proxy from './Proxy'
import Backup from './Backup'
import Storage from './Storage'
import Overview from './Overview'
import Remote from './Remote'
import TLS from './TLS'

import '@nextcloud/dialogs/styles/toast.scss'
import { generateUrl } from '@nextcloud/router'
import { showError } from '@nextcloud/dialogs'
import axios from '@nextcloud/axios'

import UtilsMixin from './UtilsMixin.js'

export default {
	name: 'App',
	mixins: [UtilsMixin],

	components: {
		AppContent,
		AppNavigation,
		AppNavigationItem,
		Overview,
		Logs,
		System,
		DynDNS, 
		StaticDNS, 
		CustomDNS,
		Remote,
		Backup,
		Storage,
		Proxy,
		TLS,
	},
	data() {
		return {
			page: 'overview',
			updating: false,
			loading: true,
			isRemoteOpen: false,
			//docsLink,
		}
	},
	
	computed: {
	},

	async mounted() {

		try {
			// we don't really care about the status, just checking if the backend is there
			const response = await axios.get(generateUrl('/apps/nextbox/forward/status'))
		} catch (e) {
			console.error(e)
			showError(t('nextbox', 'Could not fetch overview'))
		}
		this.loading = false

	},

	methods: {
		set_page(what) {
			this.page = what
			if (this.page.startsWith('remote_')) this.isRemoteOpen = true
		},
	},
}
</script>

<style>
	
input[type='text'] {
	width: 90%;
}

.warning {
	background-color: var(--color-warning);
}

.success {
	background-color: var(--color-success);
}

.error {
	background-color: var(--color-error);
}

.neutral {
	background-color: var(--color-placeholder-dark);
}

.error-txt {
	color: var(--color-error)
}


i {
	font-style: italic;
}

b {
	font-weight: 600;
}

div.section a {
	font-weight: 500 !important;
}

div.section a:hover {
	text-decoration: underline;
	font-weight: 500;
	color: #224;
}

h3 {
	font-weight: bolder;
}

/*textarea {
	flex-grow: 1;
	width: 100%;
}*/


.app-content > div {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;
	flex-grow: 1;
	top: 30px;
}

.section:not(:last-child) {
	border-bottom: 1px solid var(--color-border) !important;
}

.section {
	display: block;
	padding: 30px;
	margin: 0;
	height: fit-content !important;
}

/*.txt {
	width: 25vw;
}*/


.icon {
	/*width: 44px;
	height: 44px;*/
	opacity: 1;
	/*background-position: 14px bottom;*/
	margin-right: 8px;
	margin-left: 4px;
	background-size: 16px;
	background-repeat: no-repeat;
	display: inline-block;
	vertical-align: middle !important;
}


#app-navigation-vue > ul.app-navigation__list {
	height: 30% !important
}


</style>
