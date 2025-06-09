/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    // Always proxy /api/* to the local FastAPI instance. The frontend detects
    // the real API URL at runtime via getApiBase.ts.
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  }
};

module.exports = nextConfig;
