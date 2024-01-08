/// <reference types="jquery" />

declare namespace Nextcloud.v18 {

    interface OC extends Nextcloud.v17.OC {

    }

    interface OCP extends Nextcloud.Common.OCP {

    }

    interface humanFileSize extends Nextcloud.Common.humanFileSize {

    }

    interface WindowWithGlobals extends Nextcloud.Common.DayMonthConstants, Window {

    }

}
