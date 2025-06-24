// webapp/services/apiClient.ts
import axios from "axios";
import { getApiBase } from "../utils/getApiBase";

export const fastApi = axios.create({
  baseURL: getApiBase(),
});
