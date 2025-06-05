'use client';
import { useState } from 'react';
import { uploadFile as uploadFileSvc } from '../services/chatService';
import { validateFile } from '../utils/validateFile';

/**
 * Hook to upload files via the chat service. It exposes an `upload` function
 * and keeps track of the current loading state and resulting message.
 */
export default function useFileUpload() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const upload = async (file: File) => {
    if (!validateFile(file)) {
      setResult('invalid file');
      return;
    }
    setLoading(true);
    try {
      const res = await uploadFileSvc(file);
      setResult(res);
    } catch (err) {
      setResult('error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return { upload, result, loading };
}
