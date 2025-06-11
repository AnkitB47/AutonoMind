import { fastApi } from './apiClient';

interface SessionOpts {
  sessionId?: string;
}

export async function sendTextMessage(text: string, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const { data } = await fastApi.post('/chat', { message: text, session_id: sessionId });
  return data.reply || '...';
}

export async function sendVoice(blob: Blob, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const form = new FormData();
  form.append('file', blob, 'audio.webm');
  const { data } = await fastApi.post('/transcribe', form);
  const text = data.text || '';
  const { data: chat } = await fastApi.post('/chat', { message: text, session_id: sessionId });
  return chat.reply || '...';
}

export async function sendVoiceFile(file: Blob, lang: string) {
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  const { data } = await fastApi.post('/input/voice', form);
  return data.response || '...';
}

export async function sendSearchQuery(query: string, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const { data } = await fastApi.post('/search/web', { query, session_id: sessionId });
  return JSON.stringify(data.results) || '...';
}

export async function sendImageFile(file: File, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const form = new FormData();
  form.append('file', file);
  const { data } = await fastApi.post('/ocr', form);
  return data.text || 'uploaded';
}

export async function uploadPdfFile(file: File, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);
  const { data } = await fastApi.post('/upload', form);
  return data.message || 'uploaded';
}

export async function uploadFile(file: File, lang: string, opts: SessionOpts = {}) {
  const { sessionId } = opts;
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);
  const { data } = await fastApi.post('/upload', form);
  return data.result || data.message || 'uploaded';
}
