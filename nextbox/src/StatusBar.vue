<template>
	<div>
		<span :class="'tag ' + state">
			<span :class="'tag-icon ' + icon" />
			<span class="tag-text"><slot></slot>{{ text }}</span>
			<span class="tag-middle" />
			<span class="tag-extra">{{ extra }}</span>
		</span>
	</div>
</template>


<script>

import '@nextcloud/dialogs/styles/toast.scss'
//import { generateUrl } from '@nextcloud/router'
// import { showError, showSuccess } from '@nextcloud/dialogs'
import { showError } from '@nextcloud/dialogs'
// import axios from '@nextcloud/axios'

export default {
	name: 'StatusBar',

	components: { },

	props: {
		initIcon: String,
		initState: String,
		initText: String,
		initExtra: String,
		statusGetter: Function,
	},

	data() {
		return {
			curIcon: null,
			curState: null,
			curText: null,
			curExtra: null,

			defaultIcon: 'icon-loading-small',
			defaultState: 'neutral',
			defaultText: '',
			defaultExtra: '',

		}
	},

	computed: { 
		text() {
			return (this.curText || this.initText) || this.defaultText
		},
		icon() {
			return (this.curIcon || this.initIcon) || this.defaultIcon
		},
		state() {
			return (this.curState || this.initState) || this.defaultState
		},
		extra() {
			return (this.curExtra || this.initExtra) || this.defaultExtra
		},
	},

	async mounted() {
		if (this.statusGetter) {
			const res = this.statusGetter()
			this.curIcon = res.icon
			this.curText = res.text
			this.curState = res.state
			this.curExtra = res.extra
			// tooltip ??
		}
	 },
	
	methods: { },
}
</script>


<style scoped>

.tag {
	margin-top: 8px;
	padding: 5px;
	border-radius: var(--border-radius);
	color: var(--color-primary-text);
	width: 50vw;
	display: block;
	height: fit-content;
}

.tag-content {
	width: 100px; 
	overflow: hidden;
}

.tag-middle {
	width: 1px;
}

.tag-extra {
	/*width: 100px; */
	float: right; 
	text-align: right;
	padding-right: 10px;
}

.tag-action {
	padding-left: 8px;
	padding-right: 8px;
}

.tag-icon {
	opacity: 1;
	background-position-y: -1px;
	margin-right: 8px;
	margin-left: 4px;
	background-size: 16px;
	background-repeat: no-repeat;
	display: inline-block;
	vertical-align: middle !important;
}

</style>
