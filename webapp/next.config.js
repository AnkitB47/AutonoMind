/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // bump the Next.js Server Actions body size limit so uploads <10 MB succeed
  experimental: {
    serverActions: {
      bodySizeLimit: '10mb',
    },
  },

  async rewrites() {
    const backend = process.env.NODE_ENV === 'production'
      ? process.env.NEXT_PUBLIC_FASTAPI_URL
      : 'http://localhost:8000';

    return [
      {
        source: '/api/:path*',
        destination: `${backend}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
