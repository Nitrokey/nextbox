# @nextcloud/typings

[![Build Status](https://travis-ci.com/nextcloud/nextcloud-typings.svg?branch=master)](https://travis-ci.com/nextcloud/nextcloud-typings)

Versioned typings for the (internal) JavaScript APIs of Nextcloud used in higher level packages.

## Usage

You can use this package to verify your API usage is compatible with a range of Nextcloud versions

```ts
/// <reference types="nextcloud-typings" />

declare var OC: Nextcloud.v16.OC | Nextcloud.v17.OC | Nextcloud.v18.OC | Nextcloud.v19.OC;

OC.L10N.translate("app", "text")
```

The TypeScript compiler will translate the code above to `OC.L10N.translate("app", "text");` and throws an error if any of the Nextcloud versions in use for the [union type](https://www.typescriptlang.org/docs/handbook/advanced-types.html#union-types) do not exist on all interfaces.
