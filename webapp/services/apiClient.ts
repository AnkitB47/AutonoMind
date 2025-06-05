import axios from 'axios';

const fastApi = axios.create({ baseURL: 'http://localhost:8000' });
const streamlitApi = axios.create({ baseURL: 'http://localhost:8080' });

export { fastApi, streamlitApi };
