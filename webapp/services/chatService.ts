import axios from 'axios';
import apiClient from './apiClient';

interface SessionOpts {
  sessionId?: string;
}

export type ChatResponse = {
  reply?: string;
  image_url?: string;
  confidence?: number;
  session_id?: string;
};


export async function sendChat(
  input: string | Blob | File,
  mode: 'text' | 'voice' | 'image' | 'search',
  lang: string,
  opts: SessionOpts = {}
): Promise<ChatResponse> {
  const { sessionId } = opts;

  if (mode === 'text') {
    const { data } = await apiClient.post('/chat', {
      message: input,
      lang,
      session_id: sessionId,
    });
    return data as ChatResponse;
  } else if (mode === 'search') {
    const { data } = await apiClient.post('/input/search', {
      query: input,
      lang,
      session_id: sessionId,
    });
    return { reply: data.response || '...' };
  }

  const form = new FormData();
  form.append('file', input);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);

  if (mode === 'voice') {
    const { data } = await apiClient.post('/input/voice', form);
    return { reply: data.response || '...' };
  } else if (mode === 'image') {
    const { data } = await apiClient.post('/upload', form);
    return { reply: data.message || 'uploaded', session_id: data.session_id };
  }

  throw new Error(`Unsupported mode: ${mode}`);
}


export async function uploadFile(
  file: File,
  lang: string,
  opts: SessionOpts = {}
) {
  const { sessionId } = opts;
  const form = new FormData();
  form.append('file', file);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);
  const { data } = await apiClient.post('/upload', form);
  return data as { message: string; session_id?: string; result?: string };
}
