const path = require('path')
const webpack = require('webpack')

const StyleLintPlugin = require('stylelint-webpack-plugin')
const VueLoaderPlugin = require('vue-loader/lib/plugin')

const appName = process.env.npm_package_name
const appVersion = process.env.npm_package_version
const buildMode = process.env.NODE_ENV
const isDev = buildMode === 'development'
console.info('Building', appName, appVersion, '\n')

module.exports = {
	mode: buildMode,
	devtool: isDev ? '#cheap-source-map' : '#source-map',
	entry: {
		main: path.resolve(path.join('src', 'main.js')),
	},
	output: {
		path: path.resolve('./js'),
		publicPath: '/js/',
		filename: `${appName}-[name].js?v=[contenthash]`,
		chunkFilename: `${appName}-[name].js?v=[contenthash]`,
	},
	module: {
		rules: [
			{
				test: /\.css$/,
				use: ['style-loader', 'css-loader'],
			},
			{
				test: /\.scss$/,
				use: ['style-loader', 'css-loader', 'sass-loader'],
			},
			{
				test: /\.(js|vue)$/,
				use: 'eslint-loader',
				exclude: /node_modules/,
				enforce: 'pre',
			},
			{
				test: /\.vue$/,
				loader: 'vue-loader',
			},
			{
				test: /\.js$/,
				loader: 'babel-loader',
				exclude: /node_modules/,
			},
			{
				test: /\.(png|jpg|gif|svg)$/,
				loader: 'url-loader'
			},
		],
	},
	plugins: [
		new VueLoaderPlugin(),
		new StyleLintPlugin({
			files: 'src/**/*.{css,scss,vue}',
		}),

		// Make appName & appVersion available as a constant
		new webpack.DefinePlugin({ appName: JSON.stringify(appName) }),
		new webpack.DefinePlugin({ appVersion: JSON.stringify(appVersion) }),
	],
	resolve: {
		extensions: ['*', '.js', '.vue'],
		symlinks: false,
	},
}
