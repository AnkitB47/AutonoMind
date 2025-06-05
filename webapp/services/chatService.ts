import { fastApi, streamlitApi } from './apiClient';

export async function sendTextMessage(text: string) {
  const { data } = await streamlitApi.post('/text-chat', { text });
  return data.response || '...';
}

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await fastApi.post('/upload', form);
  return data.result || 'uploaded';
}
