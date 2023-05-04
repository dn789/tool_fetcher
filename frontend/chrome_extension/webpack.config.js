const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: {
    popup: "./src/Popup.js",
    background: "./src/background.js",
    content: "./src/content.js",
    checkType: "./src/checkType.js",
  },
  output: {
    path: path.resolve(__dirname, 'build'),
    publicPath: '',
    filename: '[name].js',
  },
  module: {
    rules: [{
      test: /\.(js|jsx)$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-env', '@babel/preset-react'],
        }
      }
    },
    {
      test: /sidebar\.css$/,
      use: ["to-string-loader", "css-loader"]
    },
    {
      test: /[^sidebar]\.css$/,
      use: ["style-loader", "css-loader"]
    },
    {
      test: /\.(png|svg|jpg|gif)$/,
      use: ["file-loader"]
    }],
  },
  plugins: [new HtmlWebpackPlugin({
    template: "./src/popup.html",
    filename: "popup.html",
    inject: false,
  }),
  new HtmlWebpackPlugin({
    template: "./src/pdf.html",
    filename: "pdf.html",
    inject: false,
  }),
  new CopyPlugin({
    patterns: [
      { from: "public" }
    ],
  }),
  ],
  mode: 'development',
  devtool: 'cheap-module-source-map'
};

