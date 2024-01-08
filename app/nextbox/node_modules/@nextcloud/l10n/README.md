# @nextcloud/l10n

[![Build Status](https://travis-ci.com/nextcloud/nextcloud-l10n.svg?branch=master)](https://travis-ci.com/nextcloud/nextcloud-l10n)
[![npm](https://img.shields.io/npm/v/@nextcloud/l10n.svg)](https://www.npmjs.com/package/@nextcloud/l10n)
[![Documentation](https://img.shields.io/badge/Documentation-online-brightgreen)](https://nextcloud.github.io/nextcloud-l10n/)

Nextcloud L10n helpers for apps and libraries.

## Installation

```
npm i -S @nextcloud/l10n
```

## Usage

### OC.L10n abstraction

You can use helpers in this package in order generate code that also works when it's not loaded on a Nextcloud page. This is primary useful for testing. The logic will just return the original string if the global variable `OC` isn't found.

In order to not break the l10n string extraction scripts, make sure to alias the imported function to match the legacy syntax:

```js
import {translate as t, translatePlural as n} from '@nextcloud/l10n'

t('myapp', 'Hello!')
n('myapp', '%n cloud', '%n clouds', 100)
```

See the [localization docs](https://docs.nextcloud.com/server/stable/developer_manual/app/view/l10n.html) for more info.

### Independent translation

You can use this package to translate your app or library independent of Nextcloud. For that you need .po(t) files. These can be extracted with [gettext-extractor](https://github.com/lukasgeiter/gettext-extractor).

```js
import { getGettextBuilder } from '@nextcloud/l10n/gettext'

const lang = 'sv'
const po = ... // Use https://github.com/smhg/gettext-parser to read and convert your .po(t) file

const gt = getGettextBuilder()
    .detectLocale()
    .addTranslation('sv', po)
    .build()
```

#### Translate single string

```js
gt.gettext('my source string')
```

#### Placeholders

```js
gt.gettext('this is a {placeholder}. and this is {key2}', {
    placeholder: 'test',
    key2: 'also a test',
})
```

See [the developer docs for general guidelines](https://docs.nextcloud.com/server/latest/developer_manual/app/view/l10n.html).

#### Translate plurals

```js
gt.ngettext('%n Mississippi', '%n Mississippi', 3)
```

See [the developer docs for general guidelines](https://docs.nextcloud.com/server/latest/developer_manual/app/view/l10n.html).
