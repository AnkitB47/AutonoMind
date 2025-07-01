'use client';
import axios from 'axios';
import { getFastApiBase } from '../services/apiClient';

export default function useImageSearch(sessionId?: string) {
  const search = async (input: string | File) => {
    const form = new FormData();
    if (typeof input === 'string') {
      form.append('text', input);
    } else {
      form.append('file', input);
    }
    if (sessionId) form.append('session_id', sessionId);
    const base = getFastApiBase();
    const { data } = await axios.post(`${base}/search/image-similarity`, form);
    return data.results as { url: string; score: number }[];
  };

  return { search };
}
