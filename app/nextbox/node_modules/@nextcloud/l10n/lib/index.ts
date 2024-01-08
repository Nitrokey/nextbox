/// <reference types="@nextcloud/typings" />

declare var OC: Nextcloud.v16.OC | Nextcloud.v17.OC | Nextcloud.v18.OC | Nextcloud.v19.OC | Nextcloud.v20.OC;
declare var window: Nextcloud.v16.WindowWithGlobals | Nextcloud.v17.WindowWithGlobals | Nextcloud.v18.WindowWithGlobals | Nextcloud.v19.WindowWithGlobals;

/**
 * Returns the user's locale
 */
export function getLocale(): string {
    if (typeof OC === 'undefined') {
        console.warn('No OC found')
        return 'en'
    }

    return OC.getLocale()
}

export function getCanonicalLocale(): string {
	return getLocale().replace(/_/g, '-')
}

/**
 * Returns the user's language
 */
export function getLanguage(): string {
    if (typeof OC === 'undefined') {
        console.warn('No OC found')
        return 'en';
    }

    return OC.getLanguage()
}

interface TranslationOptions {
    escape?: boolean
}

/**
 * Translate a string
 *
 * @param {string} app the id of the app for which to translate the string
 * @param {string} text the string to translate
 * @param {object} vars map of placeholder key to value
 * @param {number} number to replace %n with
 * @param {object} [options] options object
 * @return {string}
 */
export function translate(app: string, text: string, vars?: object, count?: number, options?: TranslationOptions): string {
    if (typeof OC === 'undefined') {
        console.warn('No OC found')
        return text
    }

    return OC.L10N.translate(app, text, vars, count, options)
}

/**
 * Translate a plural string
 *
 * @param {string} app the id of the app for which to translate the string
 * @param {string} textSingular the string to translate for exactly one object
 * @param {string} textPlural the string to translate for n objects
 * @param {number} count number to determine whether to use singular or plural
 * @param {Object} vars of placeholder key to value
 * @param {object} options options object
 * @return {string}
 */

export function translatePlural(app: string, textSingular: string, textPlural: string, count: number, vars?: object, options?: TranslationOptions): string {
    if (typeof OC === 'undefined') {
        console.warn('No OC found')
        return textSingular
    }

    return OC.L10N.translatePlural(app, textSingular, textPlural, count, vars, options)
}

/**
 * Get the first day of the week
 *
 * @return {number}
 */
export function getFirstDay(): number {
    if (typeof window.firstDay === 'undefined') {
        console.warn('No firstDay found')
        return 1
    }

    return window.firstDay
}

/**
 * Get a list of day names (full names)
 *
 * @return {string[]}
 */
export function getDayNames(): string[] {
    if (typeof window.dayNames === 'undefined') {
        console.warn('No dayNames found')
        return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    }

    return window.dayNames
}

/**
 * Get a list of day names (short names)
 *
 * @return {string[]}
 */
export function getDayNamesShort(): string[] {
    if (typeof window.dayNamesShort === 'undefined') {
        console.warn('No dayNamesShort found')
        return ['Sun.', 'Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.']
    }

    return window.dayNamesShort
}

/**
 * Get a list of day names (minified names)
 *
 * @return {string[]}
 */
export function getDayNamesMin(): string[] {
    if (typeof window.dayNamesMin === 'undefined') {
        console.warn('No dayNamesMin found')
        return ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
    }

    return window.dayNamesMin
}

/**
 * Get a list of month names (full names)
 *
 * @return {string[]}
 */
export function getMonthNames(): string[] {
    if (typeof window.monthNames === 'undefined') {
        console.warn('No monthNames found')
        return ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    }

    return window.monthNames
}

/**
 * Get a list of month names (short names)
 *
 * @return {string[]}
 */
export function getMonthNamesShort(): string[] {
    if (typeof window.monthNamesShort === 'undefined') {
        console.warn('No monthNamesShort found')
        return ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May.', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.']
    }

    return window.monthNamesShort
}
