// webapp/services/apiClient.ts
import axios from 'axios';
import getApiBase from '../utils/getApiBase';

const apiClient = axios.create({
  baseURL: getApiBase(),
});
export default apiClient;
