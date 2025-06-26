// webapp/utils/getApiBase.ts
export function getApiBase(): string {
  // Prefer a runtime value injected via env.js, then fall back to the
  // build‑time environment or the local Next.js proxy.
  if (typeof window !== 'undefined' && (window as any).RUNTIME_FASTAPI_URL) {
    return (window as any).RUNTIME_FASTAPI_URL as string;
  }
  return process.env.NEXT_PUBLIC_FASTAPI_URL || '/api';
}
