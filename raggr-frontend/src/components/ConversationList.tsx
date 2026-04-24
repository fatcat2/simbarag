import { Plus } from "lucide-react";
import { cn } from "../lib/utils";

type Conversation = {
  title: string;
  id: string;
};

type ConversationProps = {
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  onCreateNewConversation: () => void;
  selectedId?: string;
  variant?: "dark" | "light";
};

export const ConversationList = ({
  conversations,
  onSelectConversation,
  onCreateNewConversation,
  selectedId,
  variant = "dark",
}: ConversationProps) => {
  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={onCreateNewConversation}
        className={cn(
          "flex items-center gap-2 w-full px-3 py-2 rounded-xl",
          "text-sm transition-all duration-150 cursor-pointer mb-1",
          variant === "dark"
            ? "text-cream/60 hover:text-cream hover:bg-white/8"
            : "text-warm-gray hover:text-charcoal hover:bg-cream-dark",
        )}
      >
        <Plus size={14} strokeWidth={2.5} />
        <span>New thread</span>
      </button>

      {conversations.map((conv) => {
        const isActive = conv.id === selectedId;
        return (
          <button
            key={conv.id}
            onClick={() => onSelectConversation(conv)}
            className={cn(
              "w-full px-3 py-2 rounded-xl text-left",
              "text-sm truncate transition-all duration-150 cursor-pointer",
              variant === "dark"
                ? isActive
                  ? "bg-white/12 text-cream font-medium"
                  : "text-cream/60 hover:text-cream hover:bg-white/8"
                : isActive
                  ? "bg-cream-dark text-charcoal font-medium"
                  : "text-warm-gray hover:text-charcoal hover:bg-cream-dark",
            )}
          >
            {conv.title}
          </button>
        );
      })}
    </div>
  );
};
