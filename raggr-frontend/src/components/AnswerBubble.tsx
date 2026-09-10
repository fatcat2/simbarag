import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type AnswerBubbleProps = {
  text: string;
  loading?: boolean;
};

export const AnswerBubble = React.memo(({ text, loading }: AnswerBubbleProps) => {
  return (
    <div className="message-enter">
      {loading ? (
        <div className="flex items-center gap-1.5 py-1">
          <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
          <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
          <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
        </div>
      ) : (
        <div className="markdown-content text-[15px] leading-relaxed text-charcoal">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </div>
      )}
    </div>
  );
});
