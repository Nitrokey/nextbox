"use strict";

module.exports = {
	env: {
		'@nextcloud/nextcloud': true
	},
	plugins: [
		'@nextcloud',
	],
	rules: {
		'@nextcloud/no-deprecations': 'warn',
		'@nextcloud/no-removed-apis': 'error',
	},
};
