

function docsLink() {
	return '<a target="_blank" href="https://docs.nitrokey.com/nextbox/">docs.nitrokey.com/nextbox</a>'
}

function toLink(url, myLabel) {
	const label = myLabel || url
	if (!url.startsWith('http')) {
		url = `https://${url}`
	}
	return `<a target='_blank' href='${url}'>${label}</a>`
}
