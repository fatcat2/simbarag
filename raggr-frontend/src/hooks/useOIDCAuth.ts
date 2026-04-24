import { useState, useEffect } from "react";
import { userService } from "../api/userService";
import { oidcService } from "../api/oidcService";

type UseOIDCAuthOptions = {
  setAuthenticated: (isAuth: boolean) => void;
};

export function useOIDCAuth({ setAuthenticated }: UseOIDCAuthOptions) {
  const [isChecking, setIsChecking] = useState(true);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const initAuth = async () => {
      const callbackParams = oidcService.getCallbackParamsFromURL();
      if (callbackParams) {
        try {
          setIsLoggingIn(true);
          const result = await oidcService.handleCallback(
            callbackParams.code,
            callbackParams.state,
          );
          localStorage.setItem("access_token", result.access_token);
          localStorage.setItem("refresh_token", result.refresh_token);
          oidcService.clearCallbackParams();
          setAuthenticated(true);
          setIsChecking(false);
          return;
        } catch (err) {
          console.error("OIDC callback error:", err);
          setError("Login failed. Please try again.");
          oidcService.clearCallbackParams();
          setIsLoggingIn(false);
          setIsChecking(false);
          return;
        }
      }
      const isValid = await userService.validateToken();
      if (isValid) setAuthenticated(true);
      setIsChecking(false);
    };
    initAuth();
  }, [setAuthenticated]);

  const handleLogin = async () => {
    try {
      setIsLoggingIn(true);
      setError("");
      const authUrl = await oidcService.initiateLogin();
      window.location.href = authUrl;
    } catch {
      setError("Failed to initiate login. Please try again.");
      setIsLoggingIn(false);
    }
  };

  return { isChecking, isLoggingIn, error, handleLogin };
}
