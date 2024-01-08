import babel from '@rollup/plugin-babel'
import commonjs from '@rollup/plugin-commonjs'
import resolve from '@rollup/plugin-node-resolve'
import typescript from 'rollup-plugin-typescript2'

import { DEFAULT_EXTENSIONS } from '@babel/core'
const extensions = [...DEFAULT_EXTENSIONS, '.ts', '.tsx']

const packageJson = require("./package.json")

export default {
	input: 'lib/index.ts',
	output: [
		{
			file: packageJson.main,
			format: "cjs",
			sourcemap: true
		},
		{
			file: packageJson.module,
			format: "esm",
			sourcemap: true
		}
	],
	plugins: [
		resolve({ extensions }),
		typescript(),
		commonjs({ extensions }),
		babel({
			babelHelpers: 'bundled',
			extensions,
			exclude: [/core-js/],
		}),
	]
}
