import { useCallback } from "react";

export default function useAuth() {
  const setToken = useCallback((token) => {
    localStorage.setItem("fra_token", token);
  }, []);

  const clearToken = useCallback(() => {
    localStorage.removeItem("fra_token");
  }, []);

  const getToken = () => localStorage.getItem("fra_token");

  return { setToken, clearToken, getToken };
}
