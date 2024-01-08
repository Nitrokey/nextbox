import StorageBuilder from './storagebuilder'
import ScopedStorage from './scopedstorage'

export function getBuilder(appId: string): StorageBuilder {
    return new StorageBuilder(appId)
}

function clearStorage(storage: Storage, pred?: (string) => boolean): void {
    Object.keys(storage)
        .filter(k => pred ? pred(k) : true)
        .map(storage.removeItem.bind(storage))
}

export function clearAll(): void {
    const storages = [
        window.sessionStorage,
        window.localStorage,
    ]
    storages.map(s => clearStorage(s))
}

export function clearNonPersistent(): void {
    const storages = [
        window.sessionStorage,
        window.localStorage,
    ]
    storages.map(s => clearStorage(s, k => !k.startsWith(ScopedStorage.GLOBAL_SCOPE_PERSISTENT)))
}
