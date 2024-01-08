import { getRequestToken, onRequestTokenUpdate } from '../lib/index'
import { emit } from '@nextcloud/event-bus'

describe('request token', () => {
    beforeEach(() => {
        emit('csrf-token-update', {
            token: undefined,
        })
    })

    test('updates token via event', () => {
        expect(getRequestToken()).toBe(undefined)
    })

    test('find correct value', () => {
        emit('csrf-token-update', {
            token: 'token123',
        })

        expect(getRequestToken()).toBe('token123')
    })

    test('request token observer is called', () => {
        const observer = jest.fn(() => { })

        onRequestTokenUpdate(observer)
        emit('csrf-token-update', {
            token: 'token123',
        })

        expect(observer.mock.calls.length).toBe(1)
    })
})
