declare interface Toast {
	toastElement: ToastElement;
	showToast(): void;
	hideToast(): void;
}

declare interface ToastElement {
	toastify: HTMLElement;
}

declare module 'toastify-js' {

    interface ToastifyOptions {
        text?: string,
        node?: Node,
        duration?: number|null,
        destination?: string|undefined,
        newWindow?: Boolean,
        close?: Boolean,
        gravity?: string,
        selector?: string,
        /**
         * @deprecated
         */
        positionLeft?: Boolean,
        position?: String,
        avatar?: String,
        backgroundColor?: String,
        className?: String,
        stopOnFocus?: Boolean,
        callback?: Function,
        onClick?: Function,
        escapeMarkup?: boolean,
    }

    export default function Toastify(a: ToastifyOptions): Toast;

}
