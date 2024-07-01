// webpack.config.js
const path = require('path');

module.exports = {
  mode: 'development',
  entry: './arch/arch_app/assets/js/index.js',
  output: {
    filename: 'main-bundle.js',
    path: path.resolve(__dirname, 'arch/arch_app/static/arch_app/build'),
    library: 'arch',
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  }
};
