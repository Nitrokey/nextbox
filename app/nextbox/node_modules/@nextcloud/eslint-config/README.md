## @nextcloud/eslint-config

[![npm last version](https://img.shields.io/npm/v/@nextcloud/eslint-config.svg?style=flat-square)](https://www.npmjs.com/package/@nextcloud/eslint-config)
[![travis build status](https://img.shields.io/travis/com/nextcloud/eslint-config/master.svg?style=flat-square)](https://travis-ci.com/nextcloud/eslint-config)
[![Dependabot status](https://img.shields.io/badge/Dependabot-enabled-brightgreen.svg?longCache=true&style=flat-square&logo=dependabot)](https://dependabot.com)


This is a package containing the unified global eslint config used by all nextcloud apps.
It contains the necessary dependencies and peerDependencies so that other apps cannot update if this config does not support it.
Please always use dependabot to update your apps, OR pay attention to the peer dependencies error messages!


## Installation

```bash
npm install @nextcloud/eslint-config --save-dev
```

## Usage

Add a file `.eslintrc.js` in the root directory of your app repository with the following content:

```js
module.exports = {
	extends: [
		'@nextcloud',
	],
}
```

## Release new version

 1. Bump the package version with `npm version`
 2. Push version bump commit
 3. Create a new release with proper changelog https://github.com/nextcloud/eslint-config/releases/new
