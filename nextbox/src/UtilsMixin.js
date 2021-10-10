


const UtilsMixin = {
	
	data() { 
		return {
			docslink: '<a target="_blank" href="https://docs.nitrokey.com/nextbox/">docs.nitrokey.com/nextbox</a>',
			doxlink: '<a  target="_blank" href="https://docs.nitrokey.com/nextbox/">docs.nitrokey.com/nextbox</a>',
			
		}
	},
	
	methods: {
		toLink(url, myLabel) {
			const label = myLabel || url
			if (!url.startsWith('http')) {
				url = `https://${url}`
			}
			return `<a target='_blank' href='${url}'>${label}</a>`
		},

		refreshConfig() {
			// here the single most useful abstraction !!!!
			// backend-wise this will also be a signal to push 
			//    some serious config handling 
		},

		makePost(url, data, options) {

		},
	},
}


export default UtilsMixin

