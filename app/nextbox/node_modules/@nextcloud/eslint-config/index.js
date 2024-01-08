module.exports = {
	root: true,
	env: {
		browser: true,
		commonjs: true,
		es6: true,
		node: true,
		// Allow jest syntax in the src folder
		jest: true,
	},
	parserOptions: {
		parser: 'babel-eslint',
		ecmaVersion: 6,
	},
	extends: [
		'eslint:recommended',
		'plugin:import/errors',
		'plugin:import/warnings',
		'plugin:node/recommended',
		'plugin:vue/recommended',
		'plugin:@nextcloud/recommended',
		'standard',
	],
	settings: {
		'import/resolver': {
			node: {
				paths: ['src'],
				extensions: ['.js', '.vue'],
			},
		},
	},
	plugins: ['vue', 'node'],
	rules: {
		// space before function ()
		'space-before-function-paren': ['error', 'never'],
		// stay consistent with array brackets
		'array-bracket-newline': ['error', 'consistent'],
		// tabs only for indentation
		indent: ['error', 'tab'],
		'no-tabs': ['error', { allowIndentationTabs: true }],
		'vue/html-indent': ['error', 'tab'],
		// allow spaces after tabs for alignment
		'no-mixed-spaces-and-tabs': ['error', 'smart-tabs'],
		// only debug console
		'no-console': ['error', { allow: ['error', 'warn', 'info', 'debug'] }],
		// classes blocks
		'padded-blocks': ['error', { classes: 'always' }],
		// always have the operator in front
		'operator-linebreak': ['error', 'before'],
		// ternary on multiline
		'multiline-ternary': ['error', 'always-multiline'],
		// force proper JSDocs
		'valid-jsdoc': ['error', {
			prefer: {
				return: 'returns',
			},
			requireReturn: false,
			requireReturnDescription: false,
		}],
		// disallow use of "var"
		'no-var': 'error',
		// suggest using const
		'prefer-const': 'error',
		// es6 import/export and require
		'node/no-unpublished-require': ['off'],
		'node/no-unsupported-features/es-syntax': ['off'],
		// PascalCase components names for vuejs
		// https://vuejs.org/v2/style-guide/#Single-file-component-filename-casing-strongly-recommended
		'vue/component-name-in-template-casing': ['error', 'PascalCase'],
		// force name
		'vue/match-component-file-name': ['error', {
			extensions: ['jsx', 'vue', 'js'],
			shouldMatchCase: true,
		}],
		// space before self-closing elements
		'vue/html-closing-bracket-spacing': 'error',
		// no ending html tag on a new line
		'vue/html-closing-bracket-newline': ['error', { multiline: 'never' }],
		// check vue files too
		'node/no-missing-import': ['error', {
			tryExtensions: ['.js', '.vue'],
		}],
		// code spacing with attributes
		'vue/max-attributes-per-line': ['error', {
			singleline: 3,
			multiline: {
				max: 1,
				allowFirstLine: true,
			},
		}],
		// always add a trailing comma (for diff readability)
		'comma-dangle': ['warn', 'always-multiline'],
		// Allow shallow import of @vue/test-utils in order to be able to use it in 
		// the src folder
		'node/no-unpublished-import': ['error', {
			'allowModules': ['@vue/test-utils']
		}],
		// require object literal shorthand syntax
		'object-shorthand': ['error', 'always'],
	},
}
