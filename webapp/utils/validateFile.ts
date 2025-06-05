export function validateFile(file: File) {
  const valid = ['image/png', 'image/jpeg', 'application/pdf'];
  return valid.includes(file.type);
}
