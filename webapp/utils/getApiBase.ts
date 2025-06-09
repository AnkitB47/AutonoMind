export function getApiBase(): string {
  const envUrl = process.env.NEXT_PUBLIC_FASTAPI_URL;
  if (envUrl) return envUrl;
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.host}`;
  }
  return '';
}
