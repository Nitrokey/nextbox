/// <reference types="@nextcloud/typings" />

declare const OC: Nextcloud.v16.OC | Nextcloud.v17.OC | Nextcloud.v18.OC | Nextcloud.v19.OC | Nextcloud.v20.OC;

export enum FilePickerType {
    Choose = 1,
    Move = 2,
    Copy = 3,
    CopyMove = 4,
}

export class FilePicker {
    private title: string
    private multiSelect: boolean
    private mimeTypeFiler: string[]
    private modal: boolean
    private type: FilePickerType
    private directoriesAllowed: boolean
    private path?: string

    public constructor(title: string,
        multiSelect: boolean,
        mimeTypeFilter: string[],
        modal: boolean,
        type: FilePickerType,
        directoriesAllowed: boolean,
        path?: string) {
        this.title = title
        this.multiSelect = multiSelect
        this.mimeTypeFiler = mimeTypeFilter
        this.modal = modal
        this.type = type
        this.directoriesAllowed = directoriesAllowed
        this.path = path
    }

    public pick(): Promise<string> {
        return new Promise((res, rej) => {
            OC.dialogs.filepicker(
                this.title,
                res,
                this.multiSelect,
                this.mimeTypeFiler,
                this.modal,
                this.type,
                this.path,
                {
                    allowDirectoryChooser: this.directoriesAllowed
                }
            )
        })
    }
}

export class FilePickerBuilder {
    private title: string
    private multiSelect: boolean = false
    private mimeTypeFiler: string[] = []
    private modal: boolean = true
    private type: FilePickerType = FilePickerType.Choose
    private directoriesAllowed: boolean = false
    private path?: string

    public constructor(title: string) {
        this.title = title
    }

    public setMultiSelect(ms: boolean): FilePickerBuilder {
        this.multiSelect = ms
        return this
    }

    public addMimeTypeFilter(filter: string): FilePickerBuilder {
        this.mimeTypeFiler.push(filter)
        return this
    }

    public setMimeTypeFilter(filter: string[]): FilePickerBuilder {
        this.mimeTypeFiler = filter
        return this
    }

    public setModal(modal: boolean): FilePickerBuilder {
        this.modal = modal
        return this
    }

    public setType(type: FilePickerType): FilePickerBuilder {
        this.type = type
        return this
    }

    public allowDirectories(allow: boolean = true): FilePickerBuilder {
        this.directoriesAllowed = allow
        return this
    }

    public startAt(path: string): FilePickerBuilder {
        this.path = path
        return this
    }

    public build(): FilePicker {
        return new FilePicker(
            this.title,
            this.multiSelect,
            this.mimeTypeFiler,
            this.modal,
            this.type,
            this.directoriesAllowed,
            this.path
        )
    }

}

export function getFilePickerBuilder(title: string): FilePickerBuilder {
    return new FilePickerBuilder(title)
}
