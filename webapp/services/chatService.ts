import { fastApi } from './apiClient';

interface SessionOpts {
  sessionId?: string;
}

export async function sendChat(
  input: string | Blob | File,
  mode: 'text' | 'voice' | 'image' | 'search',
  lang: string,
  opts: SessionOpts = {}
) {
  const { sessionId } = opts;
  if (mode === 'text' || mode === 'search') {
    const { data } = await fastApi.post('/chat', {
      message: input,
      lang,
      session_id: sessionId
    });
    return data.reply || '...';
  }
  const form = new FormData();
  form.append('file', input);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);
  const { data } = await fastApi.post('/chat', form);
  return data.reply || '...';
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
