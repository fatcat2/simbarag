import { useState, useEffect } from "react";
import { userService } from "../api/userService";

export function useAuthCheck() {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      if (!accessToken && !refreshToken) {
        setIsChecking(false);
        setAuthenticated(false);
        return;
      }

      try {
        const me = await userService.getMe();
        setAuthenticated(true);
        setIsAdmin(me.is_admin);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setAuthenticated(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, []);

  return { isAuthenticated, isChecking, isAdmin, setAuthenticated };
}
