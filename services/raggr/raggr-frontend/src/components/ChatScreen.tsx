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

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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
      console.log(parsedConversations);
      console.log("JELLYFISH@");
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
      console.log(selectedConversation);
      console.log("JELLYFISH");
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
    if (!query.trim()) return; // Don't submit empty messages

    const currMessages = messages.concat([{ text: query, speaker: "user" }]);
    setMessages(currMessages);
    setQuery(""); // Clear input immediately after submission

    if (simbaMode) {
      console.log("simba mode activated");
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
      return;
    }

    try {
      const result = await conversationService.sendQuery(
        query,
        selectedConversation.id,
      );
      setQuestionsAnswers(
        questionsAnswers.concat([{ question: query, answer: result.response }]),
      );
      setMessages(
        currMessages.concat([{ text: result.response, speaker: "simba" }]),
      );
    } catch (error) {
      console.error("Failed to send query:", error);
      // If session expired, redirect to login
      if (error instanceof Error && error.message.includes("Session expired")) {
        setAuthenticated(false);
      }
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

  return (
    <div className="h-screen flex flex-row bg-[#F9F5EB]">
      {/* Sidebar - Expanded */}
      <aside
        className={`hidden md:flex md:flex-col bg-[#F9F5EB] border-r border-gray-200 p-4 overflow-y-auto transition-all duration-300 ${sidebarCollapsed ? "w-20" : "w-64"}`}
      >
        {!sidebarCollapsed ? (
          <div className="bg-[#F9F5EB]">
            <div className="flex flex-row items-center gap-2 mb-6">
              <img
                src={catIcon}
                alt="Simba"
                className="cursor-pointer hover:opacity-80"
                onClick={() => setSidebarCollapsed(true)}
              />
              <h2 className="text-3xl bg-[#F9F5EB] font-semibold">asksimba!</h2>
            </div>
            <ConversationList
              conversations={conversations}
              onCreateNewConversation={handleCreateNewConversation}
              onSelectConversation={handleSelectConversation}
            />
            <div className="mt-auto pt-4">
              <button
                className="w-full p-2 border border-red-400 bg-red-200 hover:bg-red-400 cursor-pointer rounded-md text-sm"
                onClick={() => setAuthenticated(false)}
              >
                logout
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <img
              src={catIcon}
              alt="Simba"
              className="cursor-pointer hover:opacity-80"
              onClick={() => setSidebarCollapsed(false)}
            />
          </div>
        )}
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Mobile header */}
        <header className="md:hidden flex flex-row justify-between items-center gap-3 p-4 border-b border-gray-200 bg-white">
          <div className="flex flex-row items-center gap-2">
            <img src={catIcon} alt="Simba" className="w-10 h-10" />
            <h1 className="text-xl">asksimba!</h1>
          </div>
          <div className="flex flex-row gap-2">
            <button
              className="p-2 border border-green-400 bg-green-200 hover:bg-green-400 cursor-pointer rounded-md text-sm"
              onClick={() => setShowConversations(!showConversations)}
            >
              {showConversations ? "hide" : "show"}
            </button>
            <button
              className="p-2 border border-red-400 bg-red-200 hover:bg-red-400 cursor-pointer rounded-md text-sm"
              onClick={() => setAuthenticated(false)}
            >
              logout
            </button>
          </div>
        </header>

        {/* Messages area */}
        {selectedConversation && (
          <div className="sticky top-0 mx-auto w-full">
            <div className="bg-[#F9F5EB] text-black px-6 w-full py-3">
              <h2 className="text-lg font-semibold">
                {selectedConversation.title || "Untitled Conversation"}
              </h2>
            </div>
          </div>
        )}
        <div className="flex-1 overflow-y-auto relative px-4 py-6">
          {/* Floating conversation name */}

          <div className="max-w-2xl mx-auto flex flex-col gap-4">
            {showConversations && (
              <div className="md:hidden">
                <ConversationList
                  conversations={conversations}
                  onCreateNewConversation={handleCreateNewConversation}
                  onSelectConversation={handleSelectConversation}
                />
              </div>
            )}
            {messages.map((msg, index) => {
              if (msg.speaker === "simba") {
                return <AnswerBubble key={index} text={msg.text} />;
              }
              return <QuestionBubble key={index} text={msg.text} />;
            })}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <footer className="p-4 bg-[#F9F5EB]">
          <div className="max-w-2xl mx-auto">
            <MessageInput
              query={query}
              handleQueryChange={handleQueryChange}
              handleKeyDown={handleKeyDown}
              handleQuestionSubmit={handleQuestionSubmit}
              setSimbaMode={setSimbaMode}
            />
          </div>
        </footer>
      </div>
    </div>
  );
};
