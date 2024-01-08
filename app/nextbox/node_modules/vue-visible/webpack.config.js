const webpack = require('webpack');
const package = require('./package.json');
const banner  =
    " VueVisible plugin v" + package.version + "\n" +
    "\n" +
    " v-visible directive for vue.\n" +
    "\n" +
    " @author "+ package.author.name +" <"+ package.author.email +">\n" +
    " "+ package.homepage +"\n" +
    " Released under the MIT License.";

module.exports = {
    entry: './src/v-visible.js',

    output: {
        path: './dist/',
        filename: 'v-visible.js',
        library: 'VueVisible',
        libraryTarget: 'umd',
        umdNamedDefine: true
    },

    resolve: {
        extensions: ['.js']
    },

    module: {
        loaders: [
            {
                test: /\.js$/,
                loader: 'babel-loader',
                include: __dirname,
                exclude: /node_modules/
            }
        ]
    },

    plugins: [
        new webpack.BannerPlugin(banner),
         new webpack.optimize.UglifyJsPlugin({
            minimize: false,
            sourceMap: false,
            mangle: false,
            compress: {
                warnings: false
            },
            output: {
                comments: true
            }
        })
    ]
};