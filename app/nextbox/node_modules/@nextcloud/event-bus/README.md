# @nextcloud/event-bus

[![Build Status](https://travis-ci.com/nextcloud/nextcloud-event-bus.svg?branch=master)](https://travis-ci.com/nextcloud/nextcloud-event-bus)
[![npm](https://img.shields.io/npm/v/@nextcloud/event-bus.svg)](https://www.npmjs.com/package/@nextcloud/event-bus)
[![Documentation](https://img.shields.io/badge/Documentation-online-brightgreen)](https://nextcloud.github.io/nextcloud-event-bus/)

A simple event bus to communicate between Nextcloud components.

## Installation

```
npm i -S @nextcloud/event-bus
```

## Usage

```js
import { emit, subscribe, unsubscribe } from '@nextcloud/event-bus'

const h = e => console.info(e)

subscribe('a', h)
subscribe('b', h)

emit('a', {
    data: 123,
})

unsubscribe('a', h)
unsubscribe('b', h)
```
