import { SimpleBus } from '../lib/SimpleBus'
import { ProxyBus } from '../lib/ProxyBus'

describe('ProxyBus', () => {
    test('proxy invalid bus', () => {
        new ProxyBus({})
    })

    test('proxy old bus', () => {
        const emit = jest.fn()

        const bus = new ProxyBus({
            getVersion() {
                return '0.0.1'
            },
            emit
        })
        bus.emit('test', { msg: 'hello' })

        expect(emit).toHaveBeenCalled()
    })

    test('proxy', () => {
        const cb = jest.fn()
        const bus = new SimpleBus()

        const proxyBus = new ProxyBus(bus)
        proxyBus.subscribe('aa', cb)
        proxyBus.emit('aa', 3)

        expect(cb).toHaveBeenCalled()
    })
})
