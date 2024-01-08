# @nextcloud/eslint-plugin

Nextcloud lint plugin for ESLint. This plugin provides a set of rules in order to check compliance of your app to the Nextcloud JavaScript API.

It is recommended to configure your app to use [`@nextcloud/eslint-config`](https://github.com/nextcloud/eslint-config) in advance. Then, this plugin is integrated automatically, but you profit also from the common Nextcloud coding standard.

## Installation

You'll first need to install [ESLint](http://eslint.org):

```
$ npm i eslint --save-dev
```

Next, install `@nextcloud/eslint-plugin`:

```
$ npm install @nextcloud/eslint-plugin --save-dev
```

## Usage

Add `plugin:nextcloud/recommended` to the `extends` section of your `.eslintrc` configuration file in order to use all recommended options (load estlint-plugin-nextcloud, add Nextcloud environment and add recommended rules):

```json
{
    "extends": [
        "plugin:nextcloud/recommended"
    ]
}
```


Alternatively, you can activate only those parts that you want to use. In this case, you have to add `nextcloud` to the plugins section of your `.eslintrc` configuration file. You can omit the `eslint-plugin-` prefix:

```json
{
    "plugins": [
        "nextcloud"
    ]
}
```


Add the Nextcloud environment if you want to use global variables defined by Nextcloud server.

```json
{
    "env": {
        "nextcloud/nextcloud": true,
    }
}
```


Configure the rules you want to use under the rules section.

```json
{
    "rules": {
        "nextcloud/no-deprecations": "warn",
        "nextcloud/no-removed-apis": "error",
    }
}
```

## Supported Shared Configurations

* `nextcloud/recommended`: Recommended configuration that loads the Nextcloud ESlint plugin, adds the Nextcloud environment and configures all recommended Nextcloud rules.


## Supported Environments

* `nextcloud/nextcloud`: Manifests global variables defined by Nextcloud server


## Supported Rules

* `nextcloud/no-deprecations`: Detects properties and functions that were deprecated in Nextcloud server
* `nextcloud/no-removed-apis`: Detects previously available APIs that were removed from Nextcloud server

