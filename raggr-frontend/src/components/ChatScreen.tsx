import { useCallback, useState, useRef } from "react";
import { LogOut, Shield, PanelLeftClose, PanelLeftOpen, Menu, X } from "lucide-react";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";
import { ToolBubble } from "./ToolBubble";
import { MessageInput } from "./MessageInput";
import { ConversationList } from "./ConversationList";
import { AdminPanel } from "./AdminPanel";
import { cn } from "../lib/utils";
import { useConversations } from "../hooks/useConversations";
import { useChat } from "../hooks/useChat";
import catIcon from "../assets/cat.png";

type ChatScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
  isAdmin: boolean;
};

export const ChatScreen = ({ setAuthenticated, isAdmin }: ChatScreenProps) => {
  const [query, setQuery] = useState("");
  const [simbaMode, setSimbaMode] = useState(false);
  const [showConversations, setShowConversations] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);

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
    selectConversation,
    createConversation,
    refreshConversations,
  } = useConversations();

  const onSessionExpired = useCallback(() => setAuthenticated(false), [setAuthenticated]);

  const {
    messages,
    setMessages,
    isLoading,
    pendingImage,
    setPendingImage,
    sendMessage,
  } = useChat({
    selectedConversation,
    createConversation,
    refreshConversations,
    onSessionExpired,
    scrollToBottom,
  });

  // Keep ref in sync for scrollToBottom behavior
  isLoadingRef.current = isLoading;

  const handleSelectConversation = useCallback(
    async (conversation: { title: string; id: string }) => {
      setShowConversations(false);
      const loaded = await selectConversation(conversation);
      setMessages(loaded);
    },
    [selectConversation, setMessages],
  );

  const handleCreateNewConversation = useCallback(async () => {
    await createConversation();
    setMessages([]);
  }, [createConversation, setMessages]);

  const handleQuestionSubmit = useCallback(() => {
    sendMessage(query, simbaMode);
    setQuery("");
  }, [query, simbaMode, sendMessage]);

  const handleQueryChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  }, []);

  const handleKeyDown = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const kev = event as unknown as React.KeyboardEvent<HTMLTextAreaElement>;
    if (kev.key === "Enter" && !kev.shiftKey) {
      kev.preventDefault();
      handleQuestionSubmit();
    }
  }, [handleQuestionSubmit]);

  const handleImageSelect = useCallback((file: File) => setPendingImage(file), [setPendingImage]);
  const handleClearImage = useCallback(() => setPendingImage(null), [setPendingImage]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAuthenticated(false);
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
          <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-4 border-b border-white/8">
              <div className="flex items-center gap-2.5">
                <img src={catIcon} alt="Simba" className="w-12 h-12" />
                <h2
                  className="text-lg font-bold text-cream tracking-tight"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  asksimba
                </h2>
              </div>
              <button
                onClick={() => setSidebarCollapsed(true)}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-cream/40 hover:text-cream hover:bg-white/10 transition-all cursor-pointer"
              >
                <PanelLeftClose size={15} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 py-3">
              <ConversationList
                conversations={conversations}
                onCreateNewConversation={handleCreateNewConversation}
                onSelectConversation={handleSelectConversation}
                selectedId={selectedConversation?.id}
              />
            </div>

            <div className="px-2 pb-3 pt-2 border-t border-white/8 flex flex-col gap-0.5">
              {isAdmin && (
                <button
                  onClick={() => setShowAdminPanel(true)}
                  className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
                >
                  <Shield size={14} />
                  <span>Admin</span>
                </button>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
              >
                <LogOut size={14} />
                <span>Sign out</span>
              </button>
            </div>
          </div>
        )}
      </aside>

      {showAdminPanel && <AdminPanel onClose={() => setShowAdminPanel(false)} />}

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
          <div className="flex items-center gap-2">
            <button
              className="w-8 h-8 rounded-xl flex items-center justify-center text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-all cursor-pointer"
              onClick={() => setShowConversations((v) => !v)}
            >
              {showConversations ? <X size={16} /> : <Menu size={16} />}
            </button>
            <button
              className="w-8 h-8 rounded-xl flex items-center justify-center text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-all cursor-pointer"
              onClick={handleLogout}
            >
              <LogOut size={15} />
            </button>
          </div>
        </header>

        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 gap-6">
            {showConversations && (
              <div className="md:hidden w-full max-w-2xl bg-warm-white rounded-2xl border border-sand-light p-3 shadow-sm">
                <ConversationList
                  conversations={conversations}
                  onCreateNewConversation={handleCreateNewConversation}
                  onSelectConversation={handleSelectConversation}
                  selectedId={selectedConversation?.id}
                  variant="light"
                />
              </div>
            )}
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
                setSimbaMode={setSimbaMode}
                isLoading={isLoading}
                pendingImage={pendingImage}
                onImageSelect={handleImageSelect}
                onClearImage={handleClearImage}
              />
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-4 py-6">
              <div className="max-w-2xl mx-auto flex flex-col gap-3">
                {showConversations && (
                  <div className="md:hidden mb-3 bg-warm-white rounded-2xl border border-sand-light p-3 shadow-sm">
                    <ConversationList
                      conversations={conversations}
                      onCreateNewConversation={handleCreateNewConversation}
                      onSelectConversation={handleSelectConversation}
                      selectedId={selectedConversation?.id}
                      variant="light"
                    />
                  </div>
                )}

                {messages.map((msg, index) => {
                  if (msg.speaker === "tool")
                    return <ToolBubble key={index} text={msg.text} />;
                  if (msg.speaker === "simba")
                    return <AnswerBubble key={index} text={msg.text} />;
                  return <QuestionBubble key={index} text={msg.text} image_key={msg.image_key} />;
                })}

                {isLoading && <AnswerBubble text="" loading={true} />}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <footer className="border-t border-sand-light/40 bg-cream">
              <div className="max-w-2xl mx-auto px-4 py-3">
                <MessageInput
                  query={query}
                  handleQueryChange={handleQueryChange}
                  handleKeyDown={handleKeyDown}
                  handleQuestionSubmit={handleQuestionSubmit}
                  setSimbaMode={setSimbaMode}
                  isLoading={isLoading}
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
