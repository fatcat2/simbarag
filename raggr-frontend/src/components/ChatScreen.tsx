import { useCallback, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { PanelLeftOpen, Menu, X } from "lucide-react";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";
import { ToolBubble } from "./ToolBubble";
import { MessageInput } from "./MessageInput";
import { SidebarContent } from "./SidebarContent";
import { AdminPanel } from "./AdminPanel";
import { ScheduledMessagesPanel } from "./ScheduledMessagesPanel";
import { cn } from "../lib/utils";
import { useConversations } from "../hooks/useConversations";
import { useChat } from "../hooks/useChat";
import catIcon from "../assets/cat.png";

type ChatScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
  isAdmin: boolean;
};

export const ChatScreen = ({ setAuthenticated, isAdmin }: ChatScreenProps) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [simbaMode, setSimbaMode] = useState(false);
  const [showConversations, setShowConversations] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [showScheduler, setShowScheduler] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isLoadingRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({
        behavior: isLoadingRef.current ? "instant" : "smooth",
      });
    });
  }, []);

  const {
    conversations,
    selectedConversation,
    createConversation,
    renameConversation,
    deleteConversation,
    refreshConversations,
  } = useConversations();

  const onSessionExpired = useCallback(() => setAuthenticated(false), [setAuthenticated]);

  const {
    messages,
    isLoading,
    messagesLoading,
    pendingImage,
    setPendingImage,
    sendMessage,
    stopGeneration,
    error,
    clearError,
  } = useChat({
    createConversation,
    refreshConversations,
    onSessionExpired,
    scrollToBottom,
  });

  // Keep ref in sync for scrollToBottom behavior
  isLoadingRef.current = isLoading;

  const handleSelectConversation = useCallback(
    (conversation: { title: string; id: string }) => {
      setShowConversations(false);
      navigate(`/c/${conversation.id}`);
    },
    [navigate],
  );

  const handleCreateNewConversation = useCallback(() => {
    setShowConversations(false);
    navigate("/");
  }, [navigate]);

  const handleQuestionSubmit = useCallback(() => {
    sendMessage(query, simbaMode);
    setQuery("");
  }, [query, simbaMode, sendMessage]);

  const handleQueryChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleQuestionSubmit();
    }
  }, [handleQuestionSubmit]);

  const handleToggleSimbaMode = useCallback(() => setSimbaMode((v) => !v), []);

  const handleDeleteConversation = useCallback(
    (id: string) => deleteConversation(id),
    [deleteConversation],
  );

  const handleImageSelect = useCallback((file: File) => setPendingImage(file), [setPendingImage]);
  const handleClearImage = useCallback(() => setPendingImage(null), [setPendingImage]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAuthenticated(false);
  };

  const sidebarProps = {
    conversations,
    onCreateNewConversation: handleCreateNewConversation,
    onSelectConversation: handleSelectConversation,
    onRenameConversation: renameConversation,
    onDeleteConversation: handleDeleteConversation,
    selectedId: selectedConversation?.id,
    isAdmin,
  };

  return (
    <div className="h-screen h-[100dvh] flex flex-row bg-cream overflow-hidden">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden md:flex md:flex-col",
          "bg-sidebar-bg transition-all duration-300 ease-in-out",
          sidebarCollapsed ? "w-[56px]" : "w-64",
        )}
      >
        {sidebarCollapsed ? (
          <div className="flex flex-col items-center py-4 gap-4 h-full">
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-cream/50 hover:text-cream hover:bg-white/10 transition-all cursor-pointer"
            >
              <PanelLeftOpen size={18} />
            </button>
            <img
              src={catIcon}
              alt="Simba"
              className="w-12 h-12 opacity-70 mt-1"
            />
          </div>
        ) : (
          <SidebarContent
            {...sidebarProps}
            onShowAdmin={() => setShowAdminPanel(true)}
            onShowScheduler={() => setShowScheduler(true)}
            onLogout={handleLogout}
            onCollapse={() => setSidebarCollapsed(true)}
          />
        )}
      </aside>

      {/* Mobile drawer */}
      {showConversations && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <aside className="w-72 max-w-[80%] h-full bg-sidebar-bg shadow-xl animate-drawer-in">
            <SidebarContent
              {...sidebarProps}
              onShowAdmin={() => {
                setShowConversations(false);
                setShowAdminPanel(true);
              }}
              onShowScheduler={() => {
                setShowConversations(false);
                setShowScheduler(true);
              }}
              onLogout={handleLogout}
              onCloseDrawer={() => setShowConversations(false)}
            />
          </aside>
          <div
            className="flex-1 bg-charcoal/40 backdrop-blur-sm"
            onClick={() => setShowConversations(false)}
          />
        </div>
      )}

      {showAdminPanel && <AdminPanel onClose={() => setShowAdminPanel(false)} />}
      {showScheduler && <ScheduledMessagesPanel onClose={() => setShowScheduler(false)} />}

      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-warm-white border-b border-sand-light/60">
          <div className="flex items-center gap-2">
            <img src={catIcon} alt="Simba" className="w-12 h-12" />
            <h1
              className="text-base font-bold text-charcoal"
              style={{ fontFamily: "var(--font-display)" }}
            >
              asksimba
            </h1>
          </div>
          <button
            className="w-8 h-8 rounded-xl flex items-center justify-center text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-all cursor-pointer"
            onClick={() => setShowConversations(true)}
            aria-label="Open menu"
          >
            <Menu size={16} />
          </button>
        </header>

        {messages.length === 0 && !messagesLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 gap-6">
            <div className="relative">
              <div className="absolute -inset-6 bg-amber-soft/20 rounded-full blur-3xl" />
              <img src={catIcon} alt="Simba" className="relative w-36 h-36" />
            </div>
            <h1
              className="text-2xl font-bold text-charcoal"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Ask me anything
            </h1>
            <div className="w-full max-w-2xl">
              <MessageInput
                query={query}
                handleQueryChange={handleQueryChange}
                handleKeyDown={handleKeyDown}
                handleQuestionSubmit={handleQuestionSubmit}
                simbaMode={simbaMode}
                onToggleSimbaMode={handleToggleSimbaMode}
                isLoading={isLoading}
                onStop={stopGeneration}
                pendingImage={pendingImage}
                onImageSelect={handleImageSelect}
                onClearImage={handleClearImage}
              />
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-4 py-6">
              <div className="max-w-3xl mx-auto flex flex-col gap-6">
                {messages.map((msg, index) => {
                  if (msg.speaker === "tool")
                    return <ToolBubble key={index} text={msg.text} />;
                  if (msg.speaker === "simba")
                    return <AnswerBubble key={index} text={msg.text} />;
                  return <QuestionBubble key={index} text={msg.text} image_key={msg.image_key} />;
                })}

                {(isLoading || messagesLoading) && <AnswerBubble text="" loading={true} />}

                {error && (
                  <div className="flex justify-center message-enter">
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200 text-xs text-red-600">
                      <span>{error}</span>
                      <button
                        onClick={clearError}
                        className="text-red-400 hover:text-red-600 transition-colors cursor-pointer"
                        aria-label="Dismiss error"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            <footer className="border-t border-sand-light/40 bg-cream">
              <div className="max-w-3xl mx-auto px-4 py-3">
                <MessageInput
                  query={query}
                  handleQueryChange={handleQueryChange}
                  handleKeyDown={handleKeyDown}
                  handleQuestionSubmit={handleQuestionSubmit}
                  simbaMode={simbaMode}
                  onToggleSimbaMode={handleToggleSimbaMode}
                  isLoading={isLoading}
                  onStop={stopGeneration}
                  pendingImage={pendingImage}
                  onImageSelect={handleImageSelect}
                  onClearImage={handleClearImage}
                />
              </div>
            </footer>
          </>
        )}
      </div>
    </div>
  );
};
