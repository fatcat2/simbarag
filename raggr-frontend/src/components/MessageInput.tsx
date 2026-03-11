import { useState } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "../lib/utils";
import { Textarea } from "./ui/textarea";

type MessageInputProps = {
  handleQueryChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleKeyDown: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleQuestionSubmit: () => void;
  setSimbaMode: (val: boolean) => void;
  query: string;
  isLoading: boolean;
};

export const MessageInput = ({
  query,
  handleKeyDown,
  handleQueryChange,
  handleQuestionSubmit,
  setSimbaMode,
  isLoading,
}: MessageInputProps) => {
  const [simbaMode, setLocalSimbaMode] = useState(false);

  const toggleSimbaMode = () => {
    const next = !simbaMode;
    setLocalSimbaMode(next);
    setSimbaMode(next);
  };

  return (
    <div
      className={cn(
        "rounded-2xl bg-warm-white border border-sand shadow-md shadow-sand/30",
        "transition-shadow duration-200 focus-within:shadow-lg focus-within:shadow-amber-soft/20",
        "focus-within:border-amber-soft/60",
      )}
    >
      {/* Textarea */}
      <Textarea
        onChange={handleQueryChange}
        onKeyDown={handleKeyDown}
        value={query}
        rows={2}
        placeholder="Ask Simba anything..."
        className="min-h-[60px] max-h-40"
      />

      {/* Bottom toolbar */}
      <div className="flex items-center justify-between px-3 pb-2.5 pt-1">
        {/* Simba mode toggle */}
        <button
          type="button"
          onClick={toggleSimbaMode}
          className="flex items-center gap-2 group cursor-pointer select-none"
        >
          <div className={cn("toggle-track", simbaMode && "checked")}>
            <div className="toggle-thumb" />
          </div>
          <span className="text-xs text-warm-gray group-hover:text-charcoal transition-colors">
            simba mode
          </span>
        </button>

        {/* Send button */}
        <button
          type="submit"
          onClick={handleQuestionSubmit}
          disabled={isLoading || !query.trim()}
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center",
            "transition-all duration-200 cursor-pointer",
            "shadow-sm",
            isLoading || !query.trim()
              ? "bg-sand text-warm-gray/50 cursor-not-allowed shadow-none"
              : "bg-amber-glow text-white hover:bg-amber-dark hover:shadow-md hover:shadow-amber-glow/30 active:scale-95",
          )}
        >
          <ArrowUp size={15} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
};
