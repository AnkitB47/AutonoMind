import axios from 'axios';

const fastApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'
});

export { fastApi };
