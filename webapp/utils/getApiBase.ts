export function getApiBase(): string {
  // Use the runtime-injected URL when available in the browser
  if (typeof window !== 'undefined' && (window as any).RUNTIME_FASTAPI_URL) {
    return (window as any).RUNTIME_FASTAPI_URL as string;
  }

  // Local development proxies through Next.js
  if (process.env.NODE_ENV !== 'production') {
    return '/api';
  }

  // Fall back to the build-time variable or localhost
  return process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';
}
