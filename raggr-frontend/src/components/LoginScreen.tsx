import { useState, useEffect } from "react";
import { userService } from "../api/userService";

type LoginScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

export const LoginScreen = ({ setAuthenticated }: LoginScreenProps) => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isChecking, setIsChecking] = useState<boolean>(true);

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      const isValid = await userService.validateToken();
      if (isValid) {
        setAuthenticated(true);
      }
      setIsChecking(false);
    };
    checkAuth();
  }, [setAuthenticated]);

  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!username || !password) {
      setError("Please enter username and password");
      return;
    }

    try {
      const result = await userService.login(username, password);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("refresh_token", result.refresh_token);
      setAuthenticated(true);
      setError("");
    } catch (err) {
      setError("Login failed. Please check your credentials.");
      console.error("Login error:", err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  // Show loading state while checking authentication
  if (isChecking) {
    return (
      <div className="h-screen bg-opacity-20">
        <div className="bg-white/85 h-screen flex items-center justify-center">
          <div className="text-center">
            <p className="text-lg sm:text-xl">Checking authentication...</p>
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
            <div className="flex flex-col gap-1">
              <div className="flex flex-grow justify-center w-full bg-amber-400 p-2">
                <h1 className="text-base sm:text-xl font-bold text-center">
                  I AM LOOKING FOR A DESIGNER. THIS APP WILL REMAIN UGLY UNTIL A
                  DESIGNER COMES.
                </h1>
              </div>
              <header className="flex flex-row justify-center gap-2 grow sticky top-0 z-10 bg-white">
                <h1 className="text-2xl sm:text-3xl">ask simba!</h1>
              </header>
              <label htmlFor="username" className="text-sm sm:text-base">
                username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={handleKeyPress}
                className="border border-s-slate-950 p-3 rounded-md min-h-[44px]"
              />
              <label htmlFor="password" className="text-sm sm:text-base">
                password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                className="border border-s-slate-950 p-3 rounded-md min-h-[44px]"
              />
              {error && (
                <div className="text-red-600 font-semibold text-sm sm:text-base">
                  {error}
                </div>
              )}
            </div>

            <button
              className="p-3 sm:p-4 min-h-[44px] border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow text-sm sm:text-base"
              onClick={handleLogin}
            >
              login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
