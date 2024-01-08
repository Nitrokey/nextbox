declare namespace Nextcloud.v17 {

    interface FilePickerOptions {
        allowDirectoryChooser: boolean
    }

    interface Dialogs {
        FILEPICKER_TYPE_CHOOSE: number;
        FILEPICKER_TYPE_MOVE: number;
        FILEPICKER_TYPE_COPY: number;
        FILEPICKER_TYPE_COPY_MOVE: number;

        filepicker(
            title: string,
            callback: Function,
            multiselect?: boolean,
            mimeTypeFilter?: Array<string>,
            modal?: boolean,
            type?: number,
            path?: string,
            options?: FilePickerOptions): void;
    }

    interface OC {
        appswebroots: any
        config: any
        coreApps: any

        requestToken: string

        getCurrentUser(): Nextcloud.Common.CurrentUser;
        isUserAdmin(): boolean;

        getRootPath(): string;
        linkTo(app: string, file: string): string;
        linkToRemoteBase(service: string): string;
        linkToRemote(service: string): string;
        linkToOCS(service: string, version: number): string;

        generateUrl(url: string, params?: object, options?: Nextcloud.Common.UrlOptions): string;
        filePath(app: string, type: string, file: string): string;
        imagePath(app: string, file: string): string;
        encodePath(path: string): string;

        getLocale(): string;
        getLanguage(): string;
        getCanonicalLocale(): string;

        dialogs: Dialogs;
        L10N: Nextcloud.Common.L10n;
        Notifications: Nextcloud.Common.Notifications;

        webroot: string
    }

    interface OCP extends Nextcloud.Common.OCP {

    }

    interface humanFileSize extends Nextcloud.Common.humanFileSize {

    }

    interface WindowWithGlobals extends Nextcloud.Common.DayMonthConstants, Window {

    }

}
