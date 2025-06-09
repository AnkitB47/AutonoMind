export function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_FASTAPI_URL;
  if (envUrl && !envUrl.includes('localhost')) return envUrl;
  // When running in the browser fall back to the Next.js proxy
  if (typeof window !== 'undefined') {
    return '/api';
  }
  // During server side rendering default to the local FastAPI instance
  return 'http://localhost:8000';
}
