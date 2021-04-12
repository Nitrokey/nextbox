<template>
	<div>
		<span :class="'tag ' + showState">
			<span :class="'tag-icon ' + showIcon" />
			<span class="tag-text" v-html="showText"></span>
			<span class="tag-middle" />
			<span class="tag-extra">{{ showExtra }}</span>
		</span>
	</div>
</template>


<script>

//import '@nextcloud/dialogs/styles/toast.scss'
//import { generateUrl } from '@nextcloud/router'
// import { showError, showSuccess } from '@nextcloud/dialogs'
//import { showError } from '@nextcloud/dialogs'
// import axios from '@nextcloud/axios'

export default {
	name: 'StatusBar',

	components: { },

	props: {
		icon: { type: String, default: null },
		state: { type: String, default: 'neutral' },
		text: { type: String, default: '' },
		extra: { type: String, default: '' },
		status: Object
	},

	data() {
		return {
			

		}
	},

	computed: { 
		showText() {
			return (this.status && 'text' in this.status) ? this.status.text : this.text
		},
		showIcon() {
			// shall be one of 'success', 'error', 'warning' and 'neutral'
			let dynamic = 'loading-small'
			// set icon based on 'this.status' member 'icon'
			if (this.status && 'icon' in this.status) {
				dynamic = this.status.icon
			// set icon based on property 'icon'
			} else if (this.icon !== null) {
				dynamic = this.icon
			// none of the above apply, so map 'this.showState' to default icon set
			} else {
				if (this.showState === 'success') dynamic = 'checkmark'
				else if (this.showState === 'error') dynamic = 'error'
				else if (this.showState === 'warning') dynamic = 'stop'
			} 
			return 'icon icon-' + dynamic
		},
		showState() {
			return (this.status && 'state' in this.status) ? this.status.state : this.state
		},
		showExtra() {
			return (this.status && 'extra' in this.status) ? this.status.extra : this.extra
		},
	},

	async mounted() { },
	
	methods: { },
}
</script>


<style scoped>

.tag {
	margin-top: 8px;
	padding: 5px;
	border-radius: var(--border-radius);
	color: var(--color-primary-text);
	width: 90%;
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
