const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function setupProxy(app) {
  const target =
    process.env.REACT_APP_DEV_PROXY_TARGET ||
    process.env.REACT_APP_API_BASE_URL ||
    'http://localhost:8000';

  const proxy = createProxyMiddleware({
    target,
    pathFilter: ['/auth', '/feed', '/sources', '/me'],
    changeOrigin: true,
    secure: false,
    logLevel: 'debug',
  });

  app.use(proxy);
};
