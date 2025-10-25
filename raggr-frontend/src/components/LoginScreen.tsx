import { useState } from "react";
import { userService } from "../api/userService";

type LoginScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

export const LoginScreen = ({ setAuthenticated }: LoginScreenProps) => {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");

  const handleLogin = async () => {
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

  return (
    <div className="h-screen bg-opacity-20">
      <div className="bg-white/85 h-screen">
        <div className="flex flex-row justify-center py-4">
          <div className="flex flex-col gap-4 min-w-xl max-w-xl">
            <div className="flex flex-col gap-1">
              <div className="flex flex-grow justify-center w-full bg-amber-400">
                <h1 className="text-xl font-bold">
                  I AM LOOKING FOR A DESIGNER. THIS APP WILL REMAIN UGLY UNTIL A
                  DESIGNER COMES.
                </h1>
              </div>
              <header className="flex flex-row justify-center gap-2 grow sticky top-0 z-10 bg-white">
                <h1 className="text-3xl">ask simba!</h1>
              </header>
              <label htmlFor="username">username</label>
              <input
                type="text"
                id="username"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="border border-s-slate-950 p-3 rounded-md"
              />
              <label htmlFor="password">password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="border border-s-slate-950 p-3 rounded-md"
              />
              {error && (
                <div className="text-red-600 font-semibold">{error}</div>
              )}
            </div>

            <button
              className="p-4 border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow"
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
