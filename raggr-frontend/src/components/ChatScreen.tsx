import { useEffect, useState, useRef } from "react";
import { LogOut, Shield, PanelLeftClose, PanelLeftOpen, Menu, X } from "lucide-react";
import { conversationService } from "../api/conversationService";
import { userService } from "../api/userService";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";
import { ToolBubble } from "./ToolBubble";
import { MessageInput } from "./MessageInput";
import { ConversationList } from "./ConversationList";
import { AdminPanel } from "./AdminPanel";
import { cn } from "../lib/utils";
import catIcon from "../assets/cat.png";

type Message = {
  text: string;
  speaker: "simba" | "user" | "tool";
};

type Conversation = {
  title: string;
  id: string;
};

type ChatScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

const TOOL_MESSAGES: Record<string, string> = {
  simba_search: "🔍 Searching Simba's records...",
  web_search: "🌐 Searching the web...",
  get_current_date: "📅 Checking today's date...",
  ynab_budget_summary: "💰 Checking budget summary...",
  ynab_search_transactions: "💳 Looking up transactions...",
  ynab_category_spending: "📊 Analyzing category spending...",
  ynab_insights: "📈 Generating budget insights...",
  obsidian_search_notes: "📝 Searching notes...",
  obsidian_read_note: "📖 Reading note...",
  obsidian_create_note: "✏️ Saving note...",
  obsidian_create_task: "✅ Creating task...",
  journal_get_today: "📔 Reading today's journal...",
  journal_get_tasks: "📋 Getting tasks...",
  journal_add_task: "➕ Adding task...",
  journal_complete_task: "✔️ Completing task...",
};

export const ChatScreen = ({ setAuthenticated }: ChatScreenProps) => {
  const [query, setQuery] = useState<string>("");
  const [simbaMode, setSimbaMode] = useState<boolean>(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showConversations, setShowConversations] = useState<boolean>(false);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [showAdminPanel, setShowAdminPanel] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isMountedRef = useRef<boolean>(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleSelectConversation = (conversation: Conversation) => {
    setShowConversations(false);
    setSelectedConversation(conversation);
    const load = async () => {
      try {
        const fetched = await conversationService.getConversation(conversation.id);
        setMessages(
          fetched.messages.map((m) => ({ text: m.text, speaker: m.speaker })),
        );
      } catch (err) {
        console.error("Failed to load messages:", err);
      }
    };
    load();
  };

  const loadConversations = async () => {
    try {
      const fetched = await conversationService.getAllConversations();
      const parsed = fetched.map((c) => ({ id: c.id, title: c.name }));
      setConversations(parsed);
      setSelectedConversation(parsed[0] ?? null);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const handleCreateNewConversation = async () => {
    const newConv = await conversationService.createConversation();
    await loadConversations();
    setSelectedConversation({ title: newConv.name, id: newConv.id });
  };

  useEffect(() => {
    loadConversations();
    userService.getMe().then((me) => setIsAdmin(me.is_admin)).catch(() => {});
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const load = async () => {
      if (!selectedConversation) return;
      try {
        const conv = await conversationService.getConversation(selectedConversation.id);
        setSelectedConversation({ id: conv.id, title: conv.name });
        setMessages(conv.messages.map((m) => ({ text: m.text, speaker: m.speaker })));
      } catch (err) {
        console.error("Failed to load messages:", err);
      }
    };
    load();
  }, [selectedConversation?.id]);

  const handleQuestionSubmit = async () => {
    if (!query.trim() || isLoading) return;

    const currMessages = messages.concat([{ text: query, speaker: "user" }]);
    setMessages(currMessages);
    setQuery("");
    setIsLoading(true);

    if (simbaMode) {
      const randomElement = simbaAnswers[Math.floor(Math.random() * simbaAnswers.length)];
      setMessages((prev) => prev.concat([{ text: randomElement, speaker: "simba" }]));
      setIsLoading(false);
      return;
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await conversationService.streamQuery(
        query,
        selectedConversation!.id,
        (event) => {
          if (!isMountedRef.current) return;
          if (event.type === "tool_start") {
            const friendly = TOOL_MESSAGES[event.tool] ?? `🔧 Using ${event.tool}...`;
            setMessages((prev) => prev.concat([{ text: friendly, speaker: "tool" }]));
          } else if (event.type === "response") {
            setMessages((prev) => prev.concat([{ text: event.message, speaker: "simba" }]));
          } else if (event.type === "error") {
            console.error("Stream error:", event.message);
          }
        },
        abortController.signal,
      );
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
      } else {
        console.error("Failed to send query:", error);
        if (error instanceof Error && error.message.includes("Session expired")) {
          setAuthenticated(false);
        }
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleQueryChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  };

  const handleKeyDown = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const kev = event as unknown as React.KeyboardEvent<HTMLTextAreaElement>;
    if (kev.key === "Enter" && !kev.shiftKey) {
      kev.preventDefault();
      handleQuestionSubmit();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAuthenticated(false);
  };

  return (
    <div className="h-screen flex flex-row bg-cream overflow-hidden">
      {/* ── Desktop Sidebar ─────────────────────────────── */}
      <aside
        className={cn(
          "hidden md:flex md:flex-col",
          "bg-sidebar-bg transition-all duration-300 ease-in-out",
          sidebarCollapsed ? "w-[56px]" : "w-64",
        )}
      >
        {sidebarCollapsed ? (
          /* Collapsed state */
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
              className="w-7 h-7 opacity-70 mt-1"
            />
          </div>
        ) : (
          /* Expanded state */
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-white/8">
              <div className="flex items-center gap-2.5">
                <img src={catIcon} alt="Simba" className="w-7 h-7" />
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

            {/* Conversations */}
            <div className="flex-1 overflow-y-auto px-2 py-3">
              <ConversationList
                conversations={conversations}
                onCreateNewConversation={handleCreateNewConversation}
                onSelectConversation={handleSelectConversation}
                selectedId={selectedConversation?.id}
              />
            </div>

            {/* Footer */}
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

      {/* Admin Panel modal */}
      {showAdminPanel && <AdminPanel onClose={() => setShowAdminPanel(false)} />}

      {/* ── Main chat area ──────────────────────────────── */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden min-w-0">
        {/* Mobile header */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-warm-white border-b border-sand-light/60">
          <div className="flex items-center gap-2">
            <img src={catIcon} alt="Simba" className="w-7 h-7" />
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

        {/* Conversation title bar */}
        {selectedConversation && (
          <div className="bg-warm-white/80 backdrop-blur-sm border-b border-sand-light/50 px-6 py-2.5">
            <p className="text-xs font-semibold text-warm-gray truncate max-w-2xl mx-auto uppercase tracking-wider">
              {selectedConversation.title || "Untitled Conversation"}
            </p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-2xl mx-auto flex flex-col gap-3">
            {/* Mobile conversation drawer */}
            {showConversations && (
              <div className="md:hidden mb-3 bg-warm-white rounded-2xl border border-sand-light p-3 shadow-sm">
                <ConversationList
                  conversations={conversations}
                  onCreateNewConversation={handleCreateNewConversation}
                  onSelectConversation={handleSelectConversation}
                  selectedId={selectedConversation?.id}
                />
              </div>
            )}

            {/* Empty state */}
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center py-24 gap-5">
                <div className="relative">
                  <div className="absolute -inset-6 bg-amber-soft/20 rounded-full blur-3xl" />
                  <img
                    src={catIcon}
                    alt="Simba"
                    className="relative w-16 h-16 opacity-50"
                  />
                </div>
                <p className="text-warm-gray/60 text-sm">
                  Ask Simba anything
                </p>
              </div>
            )}

            {messages.map((msg, index) => {
              if (msg.speaker === "tool")
                return <ToolBubble key={index} text={msg.text} />;
              if (msg.speaker === "simba")
                return <AnswerBubble key={index} text={msg.text} />;
              return <QuestionBubble key={index} text={msg.text} />;
            })}

            {isLoading && <AnswerBubble text="" loading={true} />}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <footer className="border-t border-sand-light/40 bg-cream/80 backdrop-blur-sm">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <MessageInput
              query={query}
              handleQueryChange={handleQueryChange}
              handleKeyDown={handleKeyDown}
              handleQuestionSubmit={handleQuestionSubmit}
              setSimbaMode={setSimbaMode}
              isLoading={isLoading}
            />
          </div>
        </footer>
      </div>
    </div>
  );
};
