import ScopedStorage from '../lib/scopedstorage'
import {clearNonPersistent} from '../lib/index'

describe('clearNonPersistent', () => {
    /** @type {Storage} */
    let wrapped

    /** @type {ScopedStorage} */
    let persistent

    /** @type {ScopedStorage} */
    let volatile

    beforeEach(() => {
        wrapped = window.localStorage
        persistent = new ScopedStorage('test', wrapped, true)
        volatile = new ScopedStorage('test', wrapped, false)
    })

    it('clears only volatile storages', () => {
        persistent.setItem('i1', 'hello')
        volatile.setItem('i2', 'world')

        clearNonPersistent()

        expect(persistent.getItem('i1')).not.toBeNull()
        expect(volatile.getItem('i2')).toBeNull()
    })
})
