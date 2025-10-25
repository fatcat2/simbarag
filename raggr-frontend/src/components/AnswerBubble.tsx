import ReactMarkdown from "react-markdown";

type AnswerBubbleProps = {
  text: string;
  loading?: boolean;
};

export const AnswerBubble = ({ text, loading }: AnswerBubbleProps) => {
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
