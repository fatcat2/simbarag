import ReactMarkdown from "react-markdown";
import { cn } from "../lib/utils";

type AnswerBubbleProps = {
  text: string;
  loading?: boolean;
};

export const AnswerBubble = ({ text, loading }: AnswerBubbleProps) => {
  return (
    <div className="flex justify-start message-enter">
      <div
        className={cn(
          "max-w-[78%] rounded-3xl rounded-bl-md",
          "bg-warm-white border border-sand-light/70",
          "shadow-sm shadow-sand/30",
          "overflow-hidden",
        )}
      >
        {/* amber accent bar */}
        <div className="h-0.5 w-full bg-gradient-to-r from-amber-soft via-amber-glow/50 to-transparent" />

        <div className="px-4 py-3">
          {loading ? (
            <div className="flex items-center gap-1.5 py-1 px-1">
              <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
              <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
              <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
            </div>
          ) : (
            <div className="markdown-content text-sm leading-relaxed text-charcoal">
              <ReactMarkdown>{text}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
