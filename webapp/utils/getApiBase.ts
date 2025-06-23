export function getApiBase(): string {
  const runtime =
    typeof window !== 'undefined' ? (window as any).RUNTIME_FASTAPI_URL : undefined;
  if (runtime) {
    return runtime as string;
  }
  if (process.env.NODE_ENV !== 'production') {
    return '/api';
  }
  return process.env.NEXT_PUBLIC_FASTAPI_URL || '';
}
