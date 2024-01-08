import packageJson from "../package.json";
import { Event } from "./Event.js";
import { EventBus } from "./EventBus.js";
import { EventHandler } from "./EventHandler.js";

export class SimpleBus implements EventBus {

    private handlers = new Map<string, EventHandler[]>();

    getVersion(): string {
        return packageJson.version
    }

    subscribe(name: string, handler: EventHandler): void {
        this.handlers.set(name, (this.handlers.get(name) || []).concat(handler));
    }

    unsubscribe(name: string, handler: EventHandler): void {
        this.handlers.set(name, (this.handlers.get(name) || []).filter(h => h != handler));
    }

    emit(name: string, event: Event): void {
        (this.handlers.get(name) || []).forEach(h => {
            try {
                h(event)
            } catch (e) {
                console.error('could not invoke event listener', e)
            }
        })
    }

}
