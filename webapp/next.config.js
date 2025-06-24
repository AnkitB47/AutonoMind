/** @type {import('next').NextConfig} */

// fail early when building or running in production without the backend url
if (
  process.env.NODE_ENV === 'production' &&
  !process.env.NEXT_PUBLIC_FASTAPI_URL &&
  process.env.npm_lifecycle_event !== 'lint'
) {
  console.error('Missing NEXT_PUBLIC_FASTAPI_URL in production environment');
  process.exit(1);
}

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
