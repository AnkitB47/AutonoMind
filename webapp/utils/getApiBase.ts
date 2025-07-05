export default function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const url = (window as any).RUNTIME_FASTAPI_URL;
    if (url) return url as string;
  }
  return process.env.NEXT_PUBLIC_FASTAPI_URL || '';
}
