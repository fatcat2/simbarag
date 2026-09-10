import { Route, Routes } from "react-router-dom";
import "./App.css";
import { AuthProvider } from "./contexts/AuthContext";
import { ChatScreen } from "./components/ChatScreen";
import { ConversationsPage } from "./components/ConversationsPage";
import { LoginScreen } from "./components/LoginScreen";
import { useAuthCheck } from "./hooks/useAuthCheck";
import catIcon from "./assets/cat.png";

const AppContainer = () => {
  const { isAuthenticated, isChecking, isAdmin, setAuthenticated } = useAuthCheck();

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

  if (!isAuthenticated) {
    return <LoginScreen setAuthenticated={setAuthenticated} />;
  }

  return (
    <Routes>
      <Route path="/conversations" element={<ConversationsPage />} />
      {/* One ChatScreen instance serves both the home ("/") and per-conversation
          ("/c/:id") routes. Using a single catch-all route keeps that instance
          mounted across the navigate() that fires when the first message creates
          a conversation — a remount here would abort the in-flight SSE stream
          (and drop the answer before it's persisted). */}
      <Route
        path="*"
        element={<ChatScreen setAuthenticated={setAuthenticated} isAdmin={isAdmin} />}
      />
    </Routes>
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
