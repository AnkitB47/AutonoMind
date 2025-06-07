import axios, { AxiosInstance } from 'axios';

const fastApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'
});

const streamlitApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_STREAMLIT_URL || 'http://localhost:8080'
});

/**
 * Return the Axios instance used for chat requests based on the
 * provided choice.
 */
export function getChatApi(choice: 'fastapi' | 'streamlit'): AxiosInstance {
  return choice === 'fastapi' ? fastApi : streamlitApi;
}

export { fastApi, streamlitApi };
