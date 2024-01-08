import ScopedStorage from "../lib/scopedstorage"

describe('ScopedStorage', () => {

    /** @type {Storage} */
    let wrapped

    /** @type {ScopedStorage} */
    let storage

    beforeEach(() => {
        wrapped = window.localStorage
        storage = new ScopedStorage('test', wrapped, false)
    })

    afterEach(() => {
        wrapped.clear()
    })

    it('sets an item', () => {
        storage.setItem('test', "3")

        expect(storage.getItem('test')).toEqual("3")
    })

    it('clears own data', () => {
        storage.setItem('test', "3")
        storage.clear()

        expect(storage.getItem('test')).toBeNull()
    })

    it('clears only the scoped data', () => {
        const storage2 = new ScopedStorage('test2', wrapped)

        storage.setItem('test', "3")
        storage2.clear()

        expect(storage.getItem('test')).not.toBeNull()
    })
})
