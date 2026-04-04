import { useState, useEffect } from "react";

import "./App.css";
import { AuthProvider } from "./contexts/AuthContext";
import { ChatScreen } from "./components/ChatScreen";
import { LoginScreen } from "./components/LoginScreen";
import { conversationService } from "./api/conversationService";
import catIcon from "./assets/cat.png";

const AppContainer = () => {
  const [isAuthenticated, setAuthenticated] = useState<boolean>(false);
  const [isChecking, setIsChecking] = useState<boolean>(true);

  useEffect(() => {
    const checkAuth = async () => {
      const accessToken = localStorage.getItem("access_token");
      const refreshToken = localStorage.getItem("refresh_token");

      // No tokens at all, not authenticated
      if (!accessToken && !refreshToken) {
        setIsChecking(false);
        setAuthenticated(false);
        return;
      }

      // Try to verify token by making a request
      try {
        await conversationService.getAllConversations();
        // If successful, user is authenticated
        setAuthenticated(true);
      } catch (error) {
        // Token is invalid or expired
        console.error("Authentication check failed:", error);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        setAuthenticated(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkAuth();
  }, []);

  // Show loading state while checking authentication
  if (isChecking) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-cream gap-4">
        <img
          src={catIcon}
          alt="Simba"
          className="w-16 h-16 animate-bounce"
        />
        <p className="text-warm-gray font-medium text-lg tracking-wide">
          waking up simba...
        </p>
      </div>
    );
  }

  return (
    <>
      {isAuthenticated ? (
        <ChatScreen setAuthenticated={setAuthenticated} />
      ) : (
        <LoginScreen setAuthenticated={setAuthenticated} />
      )}
    </>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContainer />
    </AuthProvider>
  );
};

export default App;
