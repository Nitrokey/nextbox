import fs from 'fs'
import gettextParser from 'gettext-parser'

import babel from '@rollup/plugin-babel'
import commonjs from '@rollup/plugin-commonjs'
import injectProcessEnv from 'rollup-plugin-inject-process-env'
import resolve from '@rollup/plugin-node-resolve'
import typescript from 'rollup-plugin-typescript2'
import BabelLoaderExcludeNodeModulesExcept from 'babel-loader-exclude-node-modules-except'

import { DEFAULT_EXTENSIONS } from '@babel/core'
const extensions = [...DEFAULT_EXTENSIONS, '.ts', '.tsx']

const packageJson = require("./package.json");

const translations = fs
	.readdirSync('./l10n')	
	.filter(name => name !== 'messages.pot' && name.endsWith('.pot'))
	.map(file => {	
		const path = './l10n/' + file	
		const locale = file.substr(0, file.length - '.pot'.length)	


		const po = fs.readFileSync(path)	
		const json = gettextParser.po.parse(po)	
		return {	
			locale,	
			json,	
		}	
	})

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
		injectProcessEnv({
			TRANSLATIONS: translations
		}),
		babel({
			babelHelpers: 'bundled',
			extensions,
			exclude: BabelLoaderExcludeNodeModulesExcept(['toastify-js']),
		}),
	]
}
