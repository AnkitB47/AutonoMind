/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    const base = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${base}/:path*`,
      },
    ];
  }
};

module.exports = nextConfig;
