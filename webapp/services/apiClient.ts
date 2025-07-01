// webapp/services/apiClient.ts
export function getFastApiBase(): string {
  if (typeof window !== 'undefined' && (window as any).RUNTIME_FASTAPI_URL) {
    return (window as any).RUNTIME_FASTAPI_URL as string;
  }
  return process.env.NEXT_PUBLIC_FASTAPI_URL ?? 'http://localhost:8000';
}
