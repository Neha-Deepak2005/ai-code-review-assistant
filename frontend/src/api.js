// One shared axios instance for the whole app.
//
// The interceptor below runs before EVERY request and attaches the JWT
// from localStorage — so no page ever has to remember to add the token.
// If the backend answers 401 (token expired/invalid), we log out and
// send the user to /login.

import axios from "axios";

const api = axios.create({
  baseURL: "/api", // Vite dev proxy forwards this to http://localhost:5000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem("token")) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
