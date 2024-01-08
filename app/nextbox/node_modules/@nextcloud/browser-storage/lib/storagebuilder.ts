
import Storage from './storage'
import ScopedStorage from './scopedstorage'

export default class StorageBuilder {

    private appId: string
    private persisted = false
    private clearedOnLogout = false

    constructor(appId: string) {
        this.appId = appId
    }

    persist(persist: boolean = true): StorageBuilder {
        this.persisted = persist
        return this
    }

    clearOnLogout(clear: boolean = true): StorageBuilder {
        this.clearedOnLogout = clear
        return this
    }

    build(): Storage {
        return new ScopedStorage(
            this.appId,
            this.persisted ? window.localStorage : window.sessionStorage,
            !this.clearedOnLogout
        )
    }

}
