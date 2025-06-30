/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
  async rewrites() {
    const target = process.env.NEXT_PUBLIC_FASTAPI_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${target}/:path*`, // forward every /api call to FastAPI
      },
    ];
  },
};

module.exports = nextConfig;
