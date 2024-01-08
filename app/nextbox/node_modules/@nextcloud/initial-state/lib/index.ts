/**
 * @param app app ID, e.g. "mail"
 * @param key name of the property
 * @param fallback optional parameter to use as default value
 * @throws if the key can't be found
 */
export function loadState<T>(app: string, key: string, fallback?: T): T {
    const elem = <HTMLInputElement>document.querySelector(`#initial-state-${app}-${key}`)
    if (elem === null) {
        if (fallback !== undefined) {
            return fallback
        }
        throw new Error(`Could not find initial state ${key} of ${app}`)
    }

    try {
        return JSON.parse(atob(elem.value))
    } catch (e) {
       throw new Error(`Could not parse initial state ${key} of ${app}`)
    }
}
