import { fastApi, streamlitApi } from './apiClient';

export async function sendTextMessage(text: string) {
  const { data } = await streamlitApi.post('/input/text', { query: text });
  return data.response || '...';
}

export async function sendVoice(blob: Blob) {
  const form = new FormData();
  form.append('file', blob, 'audio.webm');
  const { data } = await fastApi.post('/input/voice', form);
  return data.response || data.message || '...';
}

export async function sendVoiceFile(file: Blob) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await streamlitApi.post('/input/voice', form);
  return data.response || '...';
}

export async function sendSearchQuery(query: string) {
  const { data } = await streamlitApi.post('/input/search', { query });
  return data.response || '...';
}

export async function sendImageFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await fastApi.post('/input/image', form);
  return data.response || 'uploaded';
}

export async function uploadPdfFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await fastApi.post('/upload', form);
  return data.message || 'uploaded';
}
