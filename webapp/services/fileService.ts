import { fastApi } from './apiClient';

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await fastApi.post('/upload', form);
  return data.result;
}
