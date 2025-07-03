// webapp/services/apiClient.ts
import axios from 'axios';

// Use a relative base URL so requests go through Next.js rewrites in development
const apiClient = axios.create({
  baseURL: '/api',
});

export default apiClient;
