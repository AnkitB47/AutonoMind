export default function getApiBase(): string {
  // Always use /api for client-side requests to ensure Next.js rewrites work
  // window.RUNTIME_FASTAPI_URL is only used for SSR or direct backend calls
  return '/api';
}
