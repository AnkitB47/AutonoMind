export function validateFile(file: File) {
  const allowedTypes = [
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp',
  ];
  const MAX_SIZE = 10 * 1024 * 1024; // 10MB

  return allowed
