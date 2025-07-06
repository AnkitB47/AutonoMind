export default function getApiBase(): string {
  if (typeof window !== 'undefined' && (window as any).RUNTIME_FASTAPI_URL) {
    return (window as any).RUNTIME_FASTAPI_URL;
  }
  return process.env.NEXT_PUBLIC_FASTAPI_URL || '';
}
