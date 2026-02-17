
import { createAppConfig } from '@nextcloud/vite-config'
import { defineConfig } from 'vite'
import { join, resolve } from 'path'

const overrides = defineConfig({
        build: {
                emptyOutDir: false,
        },
})

export default createAppConfig(
        {
                main: resolve(join('src', 'main.js')),
        },
        {
                createEmptyCSSEntryPoints: true,
                extractLicenseInformation: true,
                thirdPartyLicense: false,
                config: overrides,
        },
)
