export function getApiBase(): string {
  // at runtime in the browser, we may have injected window.RUNTIME_FASTAPI_URL
  if (typeof window !== 'undefined' && (window as any).RUNTIME_FASTAPI_URL) {
    return (window as any).RUNTIME_FASTAPI_URL;
  }
  // in development, use the Next.js /api proxy
  if (process.env.NODE_ENV !== 'production') {
    return '/api';
  }
  // in production SSR, fall back to the env var
  return process.env.NEXT_PUBLIC_FASTAPI_URL || '';
}
