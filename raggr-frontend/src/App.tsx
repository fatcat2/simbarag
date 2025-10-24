import { useEffect, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

import "./App.css";

type QuestionAnswer = {
  question: string;
  answer: string;
};

type QuestionBubbleProps = {
  text: string;
};

type AnswerBubbleProps = {
  text: string;
  loading: string;
};

type QuestionAnswerPairProps = {
  question: string;
  answer: string;
  loading: boolean;
};

type Conversation = {
  title: string;
  id: string;
};

type Message = {
  text: string;
  speaker: "simba" | "user";
};

type ConversationMenuProps = {
  conversations: Conversation[];
};

const ConversationMenu = ({ conversations }: ConversationMenuProps) => {
  return (
    <div className="absolute bg-white w-md rounded-md shadow-xl m-4 p-4">
      <p className="py-2 px-4 rounded-md w-full text-xl font-bold">askSimba!</p>
      {conversations.map((conversation) => (
        <p className="py-2 px-4 rounded-md hover:bg-stone-200 w-full text-xl font-bold cursor-pointer">
          {conversation.title}
        </p>
      ))}
    </div>
  );
};

const QuestionBubble = ({ text }: QuestionBubbleProps) => {
  return <div className="rounded-md bg-stone-200 p-3">🤦: {text}</div>;
};

const AnswerBubble = ({ text, loading }: AnswerBubbleProps) => {
  return (
    <div className="rounded-md bg-orange-100 p-3">
      {loading ? (
        <div className="flex flex-col w-full animate-pulse gap-2">
          <div className="flex flex-row gap-2 w-full">
            <div className="bg-gray-400 w-1/2 p-3 rounded-lg" />
            <div className="bg-gray-400 w-1/2 p-3 rounded-lg" />
          </div>
          <div className="flex flex-row gap-2 w-full">
            <div className="bg-gray-400 w-1/3 p-3 rounded-lg" />
            <div className="bg-gray-400 w-2/3 p-3 rounded-lg" />
          </div>
        </div>
      ) : (
        <div className="flex flex-col">
          <ReactMarkdown>{"🐈: " + text}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};

const QuestionAnswerPair = ({
  question,
  answer,
  loading,
}: QuestionAnswerPairProps) => {
  return (
    <div className="flex flex-col gap-4">
      <QuestionBubble text={question} />
      <AnswerBubble text={answer} loading={loading} />
    </div>
  );
};

const App = () => {
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
    axios.get("/api/messages").then((result) => {
      setMessages(
        result.data.messages.map((message) => {
          return {
            text: message.text,
            speaker: message.speaker,
          };
        }),
      );
    });
  }, []);

  const handleQuestionSubmit = () => {
    let currMessages = messages.concat([{ text: query, speaker: "user" }]);
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
    const payload = { query: query };
    axios.post("/api/query", payload).then((result) => {
      setQuestionsAnswers(
        questionsAnswers.concat([
          { question: query, answer: result.data.response },
        ]),
      );
      setMessages(
        currMessages.concat([{ text: result.data.response, speaker: "simba" }]),
      );
    });
  };
  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };
  return (
    <div className="h-screen bg-opacity-20">
      <div className="bg-white/85 h-screen">
        <div className="flex flex-row justify-center py-4">
          <div className="flex flex-col gap-4 min-w-xl max-w-xl">
            <header className="flex flex-row justify-center gap-2 grow sticky top-0 z-10 bg-white">
              <h1 className="text-3xl">ask simba!</h1>
            </header>
            {/*{questionsAnswers.map((qa) => (
              <QuestionAnswerPair question={qa.question} answer={qa.answer} />
            ))}*/}
            {messages.map((msg) => {
              if (msg.speaker == "simba") {
                return <AnswerBubble text={msg.text} loading="" />;
              }

              return <QuestionBubble text={msg.text} />;
            })}
            <footer className="flex flex-col gap-2 sticky bottom-0">
              <div className="flex flex-row justify-between gap-2 grow">
                <textarea
                  type="text"
                  className="p-4 border border-blue-200 rounded-md grow bg-white"
                  onChange={handleQueryChange}
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

export default App;
