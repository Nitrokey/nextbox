/// <reference types="@nextcloud/typings" />

declare var OC: Nextcloud.v16.OC | Nextcloud.v17.OC | Nextcloud.v18.OC | Nextcloud.v19.OC | Nextcloud.v20.OC;

/**
 * Get an absolute url to a file in an app
 *
 * @param {string} app the id of the app the file belongs to
 * @param {string} file the file path relative to the app folder
 * @return {string} Absolute URL to a file
 */
export const linkTo = (app: string, file: string) => generateFilePath(app, '', file)

/**
 * Creates a relative url for remote use
 *
 * @param {string} service id
 * @return {string} the url
 */
const linkToRemoteBase = (service: string) => getRootUrl() + '/remote.php/' + service

/**
 * @brief Creates an absolute url for remote use
 * @param {string} service id
 * @return {string} the url
 */
export const generateRemoteUrl = (service: string) => window.location.protocol + '//' + window.location.host + linkToRemoteBase(service)

/**
 * Get the base path for the given OCS API service
 *
 * @param {string} service name
 * @param {int} version OCS API version
 * @return {string} OCS API base path
 */
export const generateOcsUrl = (service: string, version: Number) => {
    version = (version !== 2) ? 1 : 2
    return window.location.protocol + '//' + window.location.host + getRootUrl() + '/ocs/v' + version + '.php/' + service + '/'
}

export interface UrlOptions {
    escape: boolean,
    noRewrite: boolean
}

/**
 * Generate the absolute url for the given relative url, which can contain parameters
 *
 * Parameters will be URL encoded automatically
 *
 * @return {string} Absolute URL for the given relative URL
 */
export const generateUrl = (url: string, params?: object, options?: UrlOptions) => {
    const allOptions = Object.assign({
        escape: true,
        noRewrite: false
    }, options || {})

    const _build = function (text: string, vars: object) {
        vars = vars || {};
        return text.replace(/{([^{}]*)}/g,
            function (a: string, b: any) {
                var r = vars[b];
                if (allOptions.escape) {
                    return (typeof r === 'string' || typeof r === 'number') ? encodeURIComponent(r.toString()) : encodeURIComponent(a);
                } else {
                    return (typeof r === 'string' || typeof r === 'number') ? r.toString() : a;
                }
            }
        );
    };
    if (url.charAt(0) !== '/') {
        url = '/' + url;

    }

    if (OC.config.modRewriteWorking === true && !allOptions.noRewrite) {
        return getRootUrl() + _build(url, params || {});
    }

    return getRootUrl() + '/index.php' + _build(url, params || {});
}

/**
 * Get the absolute path to an image file
 * if no extension is given for the image, it will automatically decide
 * between .png and .svg based on what the browser supports
 *
 * @param {string} app the app id to which the image belongs
 * @param {string} file the name of the image file
 * @return {string}
 */
export const imagePath = (app: string, file: string) => {
    if (file.indexOf('.') === -1) {
        //if no extension is given, use svg
        return generateFilePath(app, 'img', file + '.svg')
    }

    return generateFilePath(app, 'img', file)
}

/**
 * Get the absolute url for a file in an app
 *
 * @param {string} app the id of the app
 * @param {string} type the type of the file to link to (e.g. css,img,ajax.template)
 * @param {string} file the filename
 * @return {string} Absolute URL for a file in an app
 */
export const generateFilePath = (app: string, type: string, file: string) => {
    const isCore = OC.coreApps.indexOf(app) !== -1
    let link = getRootUrl()
    if (file.substring(file.length - 3) === 'php' && !isCore) {
        link += '/index.php/apps/' + app;
        if (file !== 'index.php') {
            link += '/'
            if (type) {
                link += encodeURI(type + '/')
            }
            link += file
        }
    } else if (file.substring(file.length - 3) !== 'php' && !isCore) {
        link = OC.appswebroots[app];
        if (type) {
            link += '/' + type + '/'
        }
        if (link.substring(link.length - 1) !== '/') {
            link += '/'
        }
        link += file
    } else {
        if ((app === 'settings' || app === 'core' || app === 'search') && type === 'ajax') {
            link += '/index.php/'
        } else {
            link += '/'
        }
        if (!isCore) {
            link += 'apps/'
        }
        if (app !== '') {
            app += '/'
            link += app
        }
        if (type) {
            link += type + '/'
        }
        link += file
    }
    return link
}

/**
 * Return the web root path where this Nextcloud instance
 * is accessible, with a leading slash.
 * For example "/nextcloud".
 *
 * @return {string} web root path
 */
export const getRootUrl = () => OC.webroot
