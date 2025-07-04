import getApiBase from '../utils/getApiBase';

export type Mode = 'text' | 'voice' | 'image' | 'search' | 'file';

export async function sendMessage(
  sessionId: string,
  mode: Mode,
  lang: string,
  content: string | File | Blob
) {
  // 1) Files (images & PDFs) go to /upload
  if (content instanceof File) {
    const form = new FormData();
    form.append('file', content);
    form.append('session_id', sessionId);
    const res = await fetch(`${getApiBase()}/upload`, {
      method: 'POST',
      body: form,
    });
    return res.json();
  }

  // 2) Everything else streams from /chat
  const payload = typeof content === 'string'
    ? content
    : await blobToBase64(content);

  const res = await fetch(`${getApiBase()}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, mode, lang, content: payload }),
  });

  return res;
}

function blobToBase64(b: Blob): Promise<string> {
  return new Promise(resolve => {
    const reader = new FileReader();
    reader.onloadend = () =>
      resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(b);
  });
}
