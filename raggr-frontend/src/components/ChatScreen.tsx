import { useEffect, useState, useRef } from "react";
import { conversationService } from "../api/conversationService";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";
import { MessageInput } from "./MessageInput";
import { ConversationList } from "./ConversationList";
import catIcon from "../assets/cat.png";

type Message = {
  text: string;
  speaker: "simba" | "user";
};

type QuestionAnswer = {
  question: string;
  answer: string;
};

type Conversation = {
  title: string;
  id: string;
};

type ChatScreenProps = {
  setAuthenticated: (isAuth: boolean) => void;
};

export const ChatScreen = ({ setAuthenticated }: ChatScreenProps) => {
  const [query, setQuery] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [simbaMode, setSimbaMode] = useState<boolean>(false);
  const [questionsAnswers, setQuestionsAnswers] = useState<QuestionAnswer[]>(
    [],
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([
    { title: "simba meow meow", id: "uuid" },
  ]);
  const [showConversations, setShowConversations] = useState<boolean>(false);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isMountedRef = useRef<boolean>(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Cleanup effect to handle component unmounting
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      // Abort any pending requests when component unmounts
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSelectConversation = (conversation: Conversation) => {
    setShowConversations(false);
    setSelectedConversation(conversation);
    const loadMessages = async () => {
      try {
        const fetchedConversation = await conversationService.getConversation(
          conversation.id,
        );
        setMessages(
          fetchedConversation.messages.map((message) => ({
            text: message.text,
            speaker: message.speaker,
          })),
        );
      } catch (error) {
        console.error("Failed to load messages:", error);
      }
    };
    loadMessages();
  };

  const loadConversations = async () => {
    try {
      const fetchedConversations =
        await conversationService.getAllConversations();
      const parsedConversations = fetchedConversations.map((conversation) => ({
        id: conversation.id,
        title: conversation.name,
      }));
      setConversations(parsedConversations);
      setSelectedConversation(parsedConversations[0]);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const handleCreateNewConversation = async () => {
    const newConversation = await conversationService.createConversation();
    await loadConversations();
    setSelectedConversation({
      title: newConversation.name,
      id: newConversation.id,
    });
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadMessages = async () => {
      if (selectedConversation == null) return;
      try {
        const conversation = await conversationService.getConversation(
          selectedConversation.id,
        );
        // Update the conversation title in case it changed
        setSelectedConversation({
          id: conversation.id,
          title: conversation.name,
        });
        setMessages(
          conversation.messages.map((message) => ({
            text: message.text,
            speaker: message.speaker,
          })),
        );
      } catch (error) {
        console.error("Failed to load messages:", error);
      }
    };
    loadMessages();
  }, [selectedConversation?.id]);

  const handleQuestionSubmit = async () => {
    if (!query.trim() || isLoading) return; // Don't submit empty messages or while loading

    const currMessages = messages.concat([{ text: query, speaker: "user" }]);
    setMessages(currMessages);
    setQuery(""); // Clear input immediately after submission
    setIsLoading(true);

    if (simbaMode) {
      const randomIndex = Math.floor(Math.random() * simbaAnswers.length);
      const randomElement = simbaAnswers[randomIndex];
      setAnswer(randomElement);
      setQuestionsAnswers(
        questionsAnswers.concat([
          {
            question: query,
            answer: randomElement,
          },
        ]),
      );
      setIsLoading(false);
      return;
    }

    // Create a new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const result = await conversationService.sendQuery(
        query,
        selectedConversation.id,
        abortController.signal,
      );
      setQuestionsAnswers(
        questionsAnswers.concat([{ question: query, answer: result.response }]),
      );
      setMessages(
        currMessages.concat([{ text: result.response, speaker: "simba" }]),
      );
    } catch (error) {
      // Ignore abort errors (these are intentional cancellations)
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
      } else {
        console.error("Failed to send query:", error);
        // If session expired, redirect to login
        if (error instanceof Error && error.message.includes("Session expired")) {
          setAuthenticated(false);
        }
      }
    } finally {
      // Only update loading state if component is still mounted
      if (isMountedRef.current) {
        setIsLoading(false);
      }
      // Clear the abort controller reference
      abortControllerRef.current = null;
    }
  };

  const handleQueryChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(event.target.value);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, but allow Shift+Enter for new line
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleQuestionSubmit();
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAuthenticated(false);
  };

  return (
    <div className="h-screen flex flex-row bg-cream">
      {/* Sidebar */}
      <aside
        className={`hidden md:flex md:flex-col bg-sidebar-bg transition-all duration-300 ease-in-out ${
          sidebarCollapsed ? "w-[68px]" : "w-72"
        }`}
      >
        {!sidebarCollapsed ? (
          <div className="flex flex-col h-full">
            {/* Sidebar header */}
            <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
              <img
                src={catIcon}
                alt="Simba"
                className="w-9 h-9 cursor-pointer hover:scale-110 transition-transform duration-200 flex-shrink-0"
                onClick={() => setSidebarCollapsed(true)}
              />
              <h2 className="font-[family-name:var(--font-display)] text-xl font-bold text-cream tracking-tight">
                asksimba
              </h2>
            </div>

            {/* Conversations */}
            <div className="flex-1 overflow-y-auto px-3 py-3">
              <ConversationList
                conversations={conversations}
                onCreateNewConversation={handleCreateNewConversation}
                onSelectConversation={handleSelectConversation}
                selectedId={selectedConversation?.id}
              />
            </div>

            {/* Logout */}
            <div className="px-3 pb-4 pt-2 border-t border-white/10">
              <button
                className="w-full py-2.5 px-3 text-sm text-cream/60 hover:text-cream hover:bg-white/5
                  rounded-lg transition-all duration-200 cursor-pointer"
                onClick={handleLogout}
              >
                Sign out
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center py-5 h-full">
            <img
              src={catIcon}
              alt="Simba"
              className="w-9 h-9 cursor-pointer hover:scale-110 transition-transform duration-200"
              onClick={() => setSidebarCollapsed(false)}
            />
          </div>
        )}
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Mobile header */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-warm-white border-b border-sand-light">
          <div className="flex items-center gap-2.5">
            <img src={catIcon} alt="Simba" className="w-8 h-8" />
            <h1 className="font-[family-name:var(--font-display)] text-lg font-bold text-charcoal">
              asksimba
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-cream-dark text-charcoal
                hover:bg-sand-light transition-colors cursor-pointer"
              onClick={() => setShowConversations(!showConversations)}
            >
              {showConversations ? "Hide" : "Threads"}
            </button>
            <button
              className="px-3 py-1.5 text-xs font-medium rounded-lg text-warm-gray
                hover:bg-cream-dark transition-colors cursor-pointer"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </header>

        {/* Conversation title bar */}
        {selectedConversation && (
          <div className="bg-warm-white/80 backdrop-blur-sm border-b border-sand-light/50 px-6 py-3">
            <h2 className="text-sm font-semibold text-charcoal truncate max-w-2xl mx-auto">
              {selectedConversation.title || "Untitled Conversation"}
            </h2>
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-2xl mx-auto flex flex-col gap-4">
            {/* Mobile conversation list */}
            {showConversations && (
              <div className="md:hidden mb-2">
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
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="relative">
                  <div className="absolute -inset-4 bg-amber-soft/20 rounded-full blur-2xl" />
                  <img
                    src={catIcon}
                    alt="Simba"
                    className="relative w-16 h-16 opacity-60"
                  />
                </div>
                <div className="text-center">
                  <p className="text-warm-gray text-sm">
                    Ask Simba anything
                  </p>
                </div>
              </div>
            )}

            {messages.map((msg, index) => {
              if (msg.speaker === "simba") {
                return <AnswerBubble key={index} text={msg.text} />;
              }
              return <QuestionBubble key={index} text={msg.text} />;
            })}
            {isLoading && <AnswerBubble text="" loading={true} />}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <footer className="border-t border-sand-light/50 bg-warm-white/60 backdrop-blur-sm">
          <div className="max-w-2xl mx-auto px-4 py-4">
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
