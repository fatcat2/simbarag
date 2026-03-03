import { useState, useEffect } from "react";
import { userService } from "../api/userService";
import { oidcService } from "../api/oidcService";
import catIcon from "../assets/cat.png";

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
      <div className="h-screen flex flex-col items-center justify-center bg-cream gap-4">
        <img
          src={catIcon}
          alt="Simba"
          className="w-16 h-16 animate-bounce"
        />
        <p className="text-warm-gray font-medium text-lg tracking-wide">
          {isLoggingIn ? "letting you in..." : "checking credentials..."}
        </p>
      </div>
    );
  }

  return (
    <div className="h-screen bg-cream flex items-center justify-center p-4">
      {/* Decorative background texture */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, var(--color-charcoal) 1px, transparent 0)`,
          backgroundSize: '24px 24px'
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Cat icon & branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="relative mb-4">
            <div className="absolute -inset-3 bg-amber-soft/40 rounded-full blur-xl" />
            <img
              src={catIcon}
              alt="Simba"
              className="relative w-20 h-20 drop-shadow-lg"
            />
          </div>
          <h1 className="font-[family-name:var(--font-display)] text-4xl font-bold text-charcoal tracking-tight">
            asksimba
          </h1>
          <p className="text-warm-gray text-sm mt-1.5 tracking-wide">
            your feline knowledge companion
          </p>
        </div>

        {/* Login card */}
        <div className="bg-warm-white rounded-2xl shadow-lg shadow-sand/40 border border-sand-light/60 p-8">
          {error && (
            <div className="mb-4 text-sm bg-red-50 text-red-700 p-3 rounded-xl border border-red-200">
              {error}
            </div>
          )}

          <p className="text-center text-warm-gray text-sm mb-6">
            Sign in to start chatting with Simba
          </p>

          <button
            className="w-full py-3.5 px-4 bg-forest text-white font-semibold rounded-xl
              hover:bg-forest-light transition-all duration-200
              active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed
              shadow-md shadow-forest/20 hover:shadow-lg hover:shadow-forest/30
              cursor-pointer text-sm tracking-wide"
            onClick={handleOIDCLogin}
            disabled={isLoggingIn}
          >
            {isLoggingIn ? "Redirecting..." : "Sign in with Authelia"}
          </button>
        </div>

        {/* Footer paw prints */}
        <p className="text-center text-sand mt-6 text-xs tracking-widest select-none">
          ~ meow ~
        </p>
      </div>
    </div>
  );
};
