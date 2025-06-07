import { fastApi, getChatApi } from './apiClient';

export async function sendTextMessage(
  text: string,
  lang: string,
  choice: 'fastapi' | 'streamlit'
) {
  const api = getChatApi(choice);
  const { data } = await api.post('/input/text', { query: text, lang });
  return data.response || '...';
}

export async function sendVoice(blob: Blob, lang: string) {
  const form = new FormData();
  form.append('file', blob, 'audio.webm');
  form.append('lang', lang);
  const { data } = await fastApi.post('/input/voice', form);
  return data.response || data.message || '...';
}

export async function sendVoiceFile(
  file: Blob,
  lang: string,
  choice: 'fastapi' | 'streamlit'
) {
  const api = getChatApi(choice);
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  const { data } = await api.post('/input/voice', form);
  return data.response || '...';
}

export async function sendSearchQuery(
  query: string,
  lang: string,
  choice: 'fastapi' | 'streamlit'
) {
  const api = getChatApi(choice);
  const { data } = await api.post('/input/search', { query, lang });
  return data.response || '...';
}

export async function sendImageFile(file: File, lang: string) {
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  const { data } = await fastApi.post('/input/image', form);
  return data.response || 'uploaded';
}

export async function uploadPdfFile(file: File, lang: string) {
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  const { data } = await fastApi.post('/upload', form);
  return data.message || 'uploaded';
}

export async function uploadFile(file: File, lang: string) {
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  const { data } = await fastApi.post('/upload', form);
  return data.result || data.message || 'uploaded';
}
