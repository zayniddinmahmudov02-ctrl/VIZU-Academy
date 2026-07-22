import axios from "axios";

import { API_URL } from "@/src/constants/api";
import { getToken, removeToken } from "@/src/lib/token";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  console.log("API URL:", config.baseURL);
  console.log("REQUEST:", `${config.baseURL}${config.url}`);

  const token = getToken();

  const language =
    typeof window !== "undefined"
      ? localStorage.getItem("vizu-language")
      : "de";

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  config.headers["X-Language"] = language ?? "de";

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // A 401 means the token we sent is missing/invalid/expired server-side
    // — clear it so we don't keep resending a dead token on every
    // subsequent request. Each caller still handles its own error/loading
    // state; this only prevents the stale-token loop, it doesn't redirect.
    if (error.response?.status === 401) {
      removeToken();
    }

    return Promise.reject(error);
  },
);