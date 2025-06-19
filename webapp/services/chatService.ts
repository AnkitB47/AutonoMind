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

  if (mode === 'text') {
    const { data } = await fastApi.post('/input/text', {
      query: input,
      lang,
      session_id: sessionId
    });
    return data.response || '...';
  }

  if (mode === 'search') {
    const { data } = await fastApi.post('/input/search', {
      query: input,
      lang,
      session_id: sessionId
    });
    return data.response || '...';
  }

  const form = new FormData();
  form.append('file', input);
  form.append('lang', lang);
  if (sessionId) form.append('session_id', sessionId);

  if (mode === 'voice') {
    const { data } = await fastApi.post('/input/voice', form);
    return data.response || '...';
  }

  if (mode === 'image') {
    const { data } = await fastApi.post('/upload', form);
    return (data.message || 'uploaded') as string;
  }
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
  const { data } = await fastApi.post('/upload', form);
  return data as { message: string; session_id?: string; result?: string };
}
