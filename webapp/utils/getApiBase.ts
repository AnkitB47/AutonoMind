export function getApiBase(): string {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_FASTAPI_URL || '';
  }
  return `${window.location.protocol}//${window.location.host}`;
}
