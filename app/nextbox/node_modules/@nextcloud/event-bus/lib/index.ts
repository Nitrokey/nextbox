import { EventBus } from "./EventBus"
import { ProxyBus } from "./ProxyBus"
import { SimpleBus } from "./SimpleBus"

declare global {
    interface Window {
        OC: any
        _nc_event_bus: any
    }
}

function getBus(): EventBus {
    if ((typeof window.OC !== 'undefined') && window.OC._eventBus && typeof window._nc_event_bus === 'undefined') {
        console.warn('found old event bus instance at OC._eventBus. Update your version!')
        window._nc_event_bus = window.OC._eventBus
    }

    // Either use an existing event bus instance or create one
    if (typeof window._nc_event_bus !== 'undefined') {
        return new ProxyBus(window._nc_event_bus)
    } else {
        return window._nc_event_bus = new SimpleBus()
    }
}

const bus = getBus()

/**
 * Register an event listener
 *
 * @param name name of the event
 * @param handler callback invoked for every matching event emitted on the bus
 */
export function subscribe(name: string, handler: (string) => void): void {
    bus.subscribe(name, handler)
}

/**
 * Unregister a previously registered event listener
 *
 * Note: doesn't work with anonymous functions (closures). Use method of an object or store listener function in variable.
 *
 * @param name name of the event
 * @param handler callback passed to `subscribed`
 */
export function unsubscribe(name: string, handler: (string) => void): void {
    bus.unsubscribe(name, handler)
}

/**
 * Emit an event
 *
 * @param name name of the event
 * @param event event payload
 */
export function emit(name: string, event: object): void {
    bus.emit(name, event)
}
