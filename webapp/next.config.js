/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    // In development we proxy /api/* to the local FastAPI instance.
    const fastapi = process.env.NEXT_PUBLIC_FASTAPI_URL;
    if (fastapi && !fastapi.includes('localhost')) {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  }
};

module.exports = nextConfig;
