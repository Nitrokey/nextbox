import StorageBuilder from '../lib/storagebuilder'

describe('StorageBuilder', () => {

    it('build a session storage', () => {
        const builder = new StorageBuilder('mail')

        const storage = builder
            .persist()
            .build()

        expect(storage).not.toEqual(undefined)
    })

    it('build a local storage', () => {
        const builder = new StorageBuilder('mail')

        const storage = builder
            .build()

        expect(storage).not.toEqual(undefined)
    })

})
