import axios from 'axios';
import { getApiBase } from '../utils/getApiBase';

const fastApi = axios.create({
  baseURL: getApiBase()
});

export { fastApi };
