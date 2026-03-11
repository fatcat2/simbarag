import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { cn } from "../lib/utils";
import { conversationService } from "../api/conversationService";

type Conversation = {
  title: string;
  id: string;
};

type ConversationProps = {
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  onCreateNewConversation: () => void;
  selectedId?: string;
};

export const ConversationList = ({
  conversations,
  onSelectConversation,
  onCreateNewConversation,
  selectedId,
}: ConversationProps) => {
  const [items, setItems] = useState(conversations);

  useEffect(() => {
    const load = async () => {
      try {
        let fetched = await conversationService.getAllConversations();
        if (fetched.length === 0) {
          await conversationService.createConversation();
          fetched = await conversationService.getAllConversations();
        }
        setItems(fetched.map((c) => ({ id: c.id, title: c.name })));
      } catch (err) {
        console.error("Failed to load conversations:", err);
      }
    };
    load();
  }, []);

  // Keep in sync when parent updates conversations
  useEffect(() => {
    setItems(conversations);
  }, [conversations]);

  return (
    <div className="flex flex-col gap-1">
      {/* New thread button */}
      <button
        onClick={onCreateNewConversation}
        className={cn(
          "flex items-center gap-2 w-full px-3 py-2 rounded-xl",
          "text-sm text-cream/60 hover:text-cream hover:bg-white/8",
          "transition-all duration-150 cursor-pointer mb-1",
        )}
      >
        <Plus size={14} strokeWidth={2.5} />
        <span>New thread</span>
      </button>

      {/* Conversation items */}
      {items.map((conv) => {
        const isActive = conv.id === selectedId;
        return (
          <button
            key={conv.id}
            onClick={() => onSelectConversation(conv)}
            className={cn(
              "w-full px-3 py-2 rounded-xl text-left",
              "text-sm truncate transition-all duration-150 cursor-pointer",
              isActive
                ? "bg-white/12 text-cream font-medium"
                : "text-cream/60 hover:text-cream hover:bg-white/8",
            )}
          >
            {conv.title}
          </button>
        );
      })}
    </div>
  );
};
