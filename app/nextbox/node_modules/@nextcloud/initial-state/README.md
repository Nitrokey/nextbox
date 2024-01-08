# @nextcloud/initial-state

[![Build Status](https://travis-ci.com/nextcloud/nextcloud-initial-state.svg?branch=master)](https://travis-ci.com/nextcloud/nextcloud-initial-state)
[![npm](https://img.shields.io/npm/v/@nextcloud/initial-state.svg)](https://www.npmjs.com/package/@nextcloud/initial-state)
[![Documentation](https://img.shields.io/badge/Documentation-online-brightgreen)](https://nextcloud.github.io/nextcloud-initial-state/)

Access data from the server-side initial state API within apps.

## Installation

```
npm i -S @nextcloud/initial-state
```

## Usage

```js
import { loadState } from '@nextcloud/initial-state'

const val = loadState('myapp', 'user_preference')

// Provide a fallback value to return when the state is not found
const valWithFallback = loadState('myapp', 'user_preference', 'no_preference')
```

Note: `loadState` throws an `Error` if the key isn't found, hence you might want to wrap the call with a `try` block.
