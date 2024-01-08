/// <reference types="@nextcloud/typings" />

declare var OC: Nextcloud.v16.OC | Nextcloud.v17.OC | Nextcloud.v18.OC | Nextcloud.v19.OC;

const uidElement = document
	.getElementsByTagName('head')[0]
const uid = uidElement ? uidElement.getAttribute('data-user') : null

const displayNameElement = document
	.getElementsByTagName('head')[0]
const displayName = displayNameElement ? displayNameElement.getAttribute('data-user-displayname') : null

const isAdmin = (typeof OC === 'undefined')
	? false
	: OC.isUserAdmin()

export interface NextcloudUser {
	uid: String,
	displayName: String | null,
	isAdmin: Boolean,
}

export function getCurrentUser(): NextcloudUser | null {
	if (uid === null) {
		return null
	}

	return {
		uid,
		displayName,
		isAdmin,
	} as NextcloudUser
}
