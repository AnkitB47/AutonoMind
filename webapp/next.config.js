/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: "50mb",
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
  serverRuntimeConfig: {
    apiBaseUrl: 'http://localhost:8000',
  },
  publicRuntimeConfig: {
    apiBaseUrl: '/api',
  },
};

module.exports = nextConfig;
