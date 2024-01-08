import { subscribe } from '@nextcloud/event-bus'

const tokenElement = document.getElementsByTagName('head')[0]
let token = tokenElement ? tokenElement.getAttribute('data-requesttoken') : null

interface CsrfTokenObserver {
	(token: string): void;
}

const observers: Array<CsrfTokenObserver> = []

export function getRequestToken(): string | null {
	return token
}

export function onRequestTokenUpdate(observer: CsrfTokenObserver): void {
	observers.push(observer)
}

// Listen to server event and keep token in sync
subscribe('csrf-token-update', e => {
	token = e.token

	observers.forEach(observer => {
		try {
			observer(e.token)
		} catch (e) {
			console.error('error updating CSRF token observer', e)
		}
	})
})
