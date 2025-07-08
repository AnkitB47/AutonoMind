import getApiBase from '../utils/getApiBase';

export type Mode = 'text' | 'voice' | 'image' | 'search';

export async function sendMessage(
  sessionId: string,
  mode: Mode,
  lang: string,
  content: string | File | Blob
) {
  // Files (images & PDFs) go to different endpoints
  if (content instanceof File) {
    const form = new FormData();
    form.append('file', content);
    form.append('session_id', sessionId);
    const fileName = content.name.toLowerCase();
    if (fileName.endsWith('.pdf')) {
      // PDF uploads go to /upload
      const res = await fetch(`${getApiBase()}/upload`, {
        method: 'POST',
        body: form,
      });
      return res.json();
    } else if (fileName.match(/\.(png|jpg|jpeg|gif|webp)$/)) {
      // Image uploads go to /image-analyze
      const res = await fetch(`${getApiBase()}/image-analyze`, {
        method: 'POST',
        body: form,
      });
      return res.json();
    }
    // For other file types, fallback to /upload
    const res = await fetch(`${getApiBase()}/upload`, {
      method: 'POST',
      body: form,
    });
    return res.json();
  }

  // Everything else streams from /chat endpoint
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

export async function laionSearchImage(file: File, topK: number = 5) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('top_k', String(topK));
  const res = await fetch(`/api/laion-search-image`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('LAION search failed');
  return res.json();
}

function blobToBase64(b: Blob): Promise<string> {
  return new Promise(resolve => {
    const reader = new FileReader();
    reader.onloadend = () =>
      resolve((reader.result as string).split(',')[1]);
    reader.readAsDataURL(b);
  });
}
