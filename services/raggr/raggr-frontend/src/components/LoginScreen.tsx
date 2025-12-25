import { useState, useEffect } from "react";
import { userService } from "../api/userService";
import { oidcService } from "../api/oidcService";

type LoginScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

export const LoginScreen = ({ setAuthenticated }: LoginScreenProps) => {
  const [error, setError] = useState<string>("");
  const [isChecking, setIsChecking] = useState<boolean>(true);
  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);

  useEffect(() => {
    const initAuth = async () => {
      // First, check for OIDC callback parameters
      const callbackParams = oidcService.getCallbackParamsFromURL();

      if (callbackParams) {
        // Handle OIDC callback
        try {
          setIsLoggingIn(true);
          const result = await oidcService.handleCallback(
            callbackParams.code,
            callbackParams.state
          );

          // Store tokens
          localStorage.setItem("access_token", result.access_token);
          localStorage.setItem("refresh_token", result.refresh_token);

          // Clear URL parameters
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

      // Check if user is already authenticated
      const isValid = await userService.validateToken();
      if (isValid) {
        setAuthenticated(true);
      }
      setIsChecking(false);
    };

    initAuth();
  }, [setAuthenticated]);

  const handleOIDCLogin = async () => {
    try {
      setIsLoggingIn(true);
      setError("");

      // Get authorization URL from backend
      const authUrl = await oidcService.initiateLogin();

      // Redirect to Authelia
      window.location.href = authUrl;
    } catch (err) {
      setError("Failed to initiate login. Please try again.");
      console.error("OIDC login error:", err);
      setIsLoggingIn(false);
    }
  };

  // Show loading state while checking authentication or processing callback
  if (isChecking || isLoggingIn) {
    return (
      <div className="h-screen bg-opacity-20">
        <div className="bg-white/85 h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-lg sm:text-xl">
              {isLoggingIn ? "Logging in..." : "Checking authentication..."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-opacity-20">
      <div className="bg-white/85 h-screen">
        <div className="flex flex-row justify-center py-4">
          <div className="flex flex-col gap-4 w-full px-4 sm:w-11/12 sm:max-w-2xl lg:max-w-4xl sm:px-0">
            <div className="flex flex-col gap-4">
              <div className="flex flex-grow justify-center w-full bg-amber-400 p-2">
                <h1 className="text-base sm:text-xl font-bold text-center">
                  I AM LOOKING FOR A DESIGNER. THIS APP WILL REMAIN UGLY UNTIL A
                  DESIGNER COMES.
                </h1>
              </div>
              <header className="flex flex-row justify-center gap-2 grow sticky top-0 z-10 bg-white">
                <h1 className="text-2xl sm:text-3xl">ask simba!</h1>
              </header>

              {error && (
                <div className="text-red-600 font-semibold text-sm sm:text-base bg-red-50 p-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="text-center text-sm sm:text-base text-gray-600 py-2">
                Click below to login with Authelia
              </div>
            </div>

            <button
              className="p-3 sm:p-4 min-h-[44px] border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow text-sm sm:text-base font-semibold"
              onClick={handleOIDCLogin}
              disabled={isLoggingIn}
            >
              {isLoggingIn ? "Redirecting..." : "Login with Authelia"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
