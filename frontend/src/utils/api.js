import axios from "axios";

// Set backend base URL here or via .env
// .env example: VITE_API_BASE_URL="http://localhost:8000"
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});


// Optional: auth token injection
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fra_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
