import axios from '../lib/index'
import { emit } from '@nextcloud/event-bus'

it('has garbled token in test by default', () => {
    expect(axios.defaults.headers.requesttoken).toBeNull()
})

it('has the latest request token', () => {
    emit('csrf-token-update', {
        token: 'ABC123',
    })

    expect(axios.defaults.headers.requesttoken).toBe('ABC123')
})

it('has a cancel token prop', () => {
    expect(axios.CancelToken).not.toBe(undefined)
})

it('creates a new cancel token', () => {
    const token = axios.CancelToken.source()

    expect(token).not.toBe(undefined)
    expect(token.token).not.toBe(undefined)
})
