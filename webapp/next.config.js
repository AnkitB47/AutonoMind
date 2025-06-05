/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  env: {
    NEXT_PUBLIC_FASTAPI_URL:
      process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000',
    NEXT_PUBLIC_STREAMLIT_URL:
      process.env.NEXT_PUBLIC_STREAMLIT_URL || 'http://localhost:8080'
  }
};

module.exports = nextConfig;
