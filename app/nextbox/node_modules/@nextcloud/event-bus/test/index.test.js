import { emit, subscribe, unsubscribe } from '../lib/index'

test('readme example', () => {
    const h = jest.fn()

    subscribe('a', h)
    subscribe('b', h)
    emit('a', {
        data: 123,
    })
    unsubscribe('a', h)
    unsubscribe('b', h)

    expect(h.mock.calls.length).toBe(1)
})

test('unsubscribe', () => {
    const h = jest.fn()

    subscribe('a', h)
    emit('a', {
        data: 123,
    })
    unsubscribe('a', h)
    emit('a', {
        data: 123,
    })

    expect(h.mock.calls.length).toBe(1)
})
