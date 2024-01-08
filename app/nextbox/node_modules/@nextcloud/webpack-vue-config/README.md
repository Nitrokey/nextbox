# Webpack vue base config

Use this base config package to cleanup all your complicated setups and rely on automated dependencies updates.

## How-to
:warning: Make sure to have all the peer dependencies installed 

```js
// webpack.js

const webpackConfig = require('@nextcloud/webpack-vue-config')

module.exports = webpackConfig
```

```json
// package.json

...
"scripts": {
		"build": "NODE_ENV=production webpack --progress --hide-modules --config webpack.js",
		"dev": "NODE_ENV=development webpack --progress --config webpack.js",
		"watch": "NODE_ENV=development webpack --progress --watch --config webpack.js",
}
...
```

## Extend with your own configs
Here is an example on how to add your own  config to the base one

```js
// webpack.js

const { merge } = require('webpack-merge')
const path = require('path')
const webpack = require('webpack')
const webpackConfig = require('@nextcloud/webpack-vue-config')

const config = {
	entry: {
		'files-action': path.join(__dirname, 'src', 'files_action.js'),
	},
	plugins: [
		new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
	],
}

module.exports = merge(config, webpackConfig)
```
### Override duplicate tests
If you want to overrride a rule that is already provided by this package, you can use the following to replace duplicates:

```js
// webpack.js

const { merge } = require('webpack-merge')
const webpackConfig = require('@nextcloud/webpack-vue-config')

const config = {
	module: {
		rules: [
			{
				test: /\.js$/,
				loader: 'babel-loader',
				exclude: /node_modules(?!(\/|\\)(hot-patcher|webdav|camelcase)(\/|\\))/,
			},
		],
	},
}

const mergedConfigs = merge(config, webpackConfig)

// Remove duplicate rules by the `test` key
mergedConfigs.module.rules = mergedConfigs.module.rules.filter((v, i, a) => a.findIndex(t => (t.test.toString() === v.test.toString())) === i)

// Merge rules by replacing existing tests
module.exports = mergedConfigs
```

### Target and remove specific rule
If you want to remove a rule (the js for example), extract the test value from this package rules list. e.g. `/\.js$/`

:warning: Watch out for string escaping. Regex can be different than the required string: `/\.js$/` vs `/\\.js$/`

```js
// webpack.js

const { merge } = require('webpack-merge')
const webpackConfig = require('@nextcloud/webpack-vue-config')

const config = {
	module: {
		rules: [
			{
				// vue-plyr uses .mjs file
				test: /\.m?js$/,
				loader: 'babel-loader',
				exclude: /node_modules(?!(\/|\\)(camelcase|fast-xml-parser|hot-patcher|vue-plyr|webdav)(\/|\\))/,
			},
		],
	},
}

const mergedConfigs = merge(config, webpackConfig)

// Remove default js rule
const jsRuleIndex = mergedConfigs.module.rules.findIndex(rule => rule.test.toString() === '/\\.js$/')
mergedConfigs.module.rules.splice(jsRuleIndex, 1)

// Merge rules by replacing existing tests
module.exports = mergedConfigs
```
