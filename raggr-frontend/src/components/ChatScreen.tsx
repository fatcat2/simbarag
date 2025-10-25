import { useEffect, useState } from "react";
import { conversationService } from "../api/conversationService";
import { QuestionBubble } from "./QuestionBubble";
import { AnswerBubble } from "./AnswerBubble";

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

  const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

  useEffect(() => {
    const loadMessages = async () => {
      try {
        const conversation = await conversationService.getMessages();
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
  }, []);

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
      const result = await conversationService.sendQuery(query);
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
          <div className="flex flex-col gap-4 min-w-xl max-w-xl">
            <div className="flex flex-row justify-between">
              <header className="flex flex-row justify-center gap-2 grow sticky top-0 z-10 bg-white">
                <h1 className="text-3xl">ask simba!</h1>
              </header>
              <button
                className="p-4 border border-red-400 bg-red-200 hover:bg-red-400 cursor-pointer rounded-md"
                onClick={() => setAuthenticated(false)}
              >
                logout
              </button>
            </div>
            {messages.map((msg, index) => {
              if (msg.speaker === "simba") {
                return <AnswerBubble key={index} text={msg.text} />;
              }
              return <QuestionBubble key={index} text={msg.text} />;
            })}
            <footer className="flex flex-col gap-2 sticky bottom-0">
              <div className="flex flex-row justify-between gap-2 grow">
                <textarea
                  className="p-4 border border-blue-200 rounded-md grow bg-white"
                  onChange={handleQueryChange}
                  value={query}
                />
              </div>
              <div className="flex flex-row justify-between gap-2 grow">
                <button
                  className="p-4 border border-blue-400 bg-blue-200 hover:bg-blue-400 cursor-pointer rounded-md flex-grow"
                  onClick={() => handleQuestionSubmit()}
                  type="submit"
                >
                  Submit
                </button>
              </div>
              <div className="flex flex-row justify-center gap-2 grow">
                <input
                  type="checkbox"
                  onChange={(event) => setSimbaMode(event.target.checked)}
                />
                <p>simba mode?</p>
              </div>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
};
