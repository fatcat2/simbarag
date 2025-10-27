import { useEffect, useState } from "react";
import { conversationService } from "../api/conversationService";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";
import { ConversationList } from "./ConversationList";
import { parse } from "node:path/win32";

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

  const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

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
    const loadMessages = async () => {
      if (selectedConversation == null) return;
      try {
        const conversation = await conversationService.getConversation(
          selectedConversation.id,
        );
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
  }, [selectedConversation]);

  const handleQuestionSubmit = async () => {
    const currMessages = messages.concat([{ text: query, speaker: "user" }]);
    setMessages(currMessages);

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
      setQuery(""); // Clear input after successful send
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

  return (
    <div className="h-screen bg-opacity-20">
      <div className="bg-white/85 h-screen">
        <div className="flex flex-row justify-center py-4">
          <div className="flex flex-col gap-4 w-full px-4 sm:w-11/12 sm:max-w-2xl lg:max-w-4xl sm:px-0">
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-0 sm:justify-between">
              <header className="flex flex-row justify-center gap-2 sticky top-0 z-10 bg-white">
                <h1 className="text-2xl sm:text-3xl">ask simba!</h1>
              </header>
              <div className="flex flex-row gap-2 justify-center sm:justify-end">
                <button
                  className="p-2 h-11 border border-green-400 bg-green-200 hover:bg-green-400 cursor-pointer rounded-md text-sm sm:text-base"
                  onClick={() => setShowConversations(!showConversations)}
                >
                  {showConversations
                    ? "hide conversations"
                    : "show conversations"}
                </button>
                <button
                  className="p-2 h-11 border border-red-400 bg-red-200 hover:bg-red-400 cursor-pointer rounded-md text-sm sm:text-base"
                  onClick={() => setAuthenticated(false)}
                >
                  logout
                </button>
              </div>
            </div>
            {showConversations && (
              <ConversationList
                conversations={conversations}
                onCreateNewConversation={handleCreateNewConversation}
                onSelectConversation={handleSelectConversation}
              />
            )}
            {messages.map((msg, index) => {
              if (msg.speaker === "simba") {
                return <AnswerBubble key={index} text={msg.text} />;
              }
              return <QuestionBubble key={index} text={msg.text} />;
            })}
            <footer className="flex flex-col gap-2 sticky bottom-0">
              <div className="flex flex-row justify-between gap-2 grow">
                <textarea
                  className="p-3 sm:p-4 border border-blue-200 rounded-md grow bg-white min-h-[44px] resize-y"
                  onChange={handleQueryChange}
                  value={query}
                  rows={2}
                />
              </div>
              <div className="flex flex-row justify-between gap-2 grow">
                <button
                  className="p-3 sm:p-4 min-h-[44px] border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow text-sm sm:text-base"
                  onClick={() => handleQuestionSubmit()}
                  type="submit"
                >
                  Submit
                </button>
              </div>
              <div className="flex flex-row justify-center gap-2 grow items-center">
                <input
                  type="checkbox"
                  onChange={(event) => setSimbaMode(event.target.checked)}
                  className="w-5 h-5 cursor-pointer"
                />
                <p className="text-sm sm:text-base">simba mode?</p>
              </div>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
};
