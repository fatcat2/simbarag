import { useEffect, useRef, useState } from "react";
import { Check, MoreHorizontal, Pencil, Plus, Trash2, X } from "lucide-react";
import { cn } from "../lib/utils";

type Conversation = {
  title: string;
  id: string;
};

type ConversationProps = {
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  onCreateNewConversation: () => void;
  onRenameConversation?: (id: string, title: string) => void;
  onDeleteConversation?: (id: string) => void;
  selectedId?: string;
  variant?: "dark" | "light";
};

export const ConversationList = ({
  conversations,
  onSelectConversation,
  onCreateNewConversation,
  onRenameConversation,
  onDeleteConversation,
  selectedId,
  variant = "dark",
}: ConversationProps) => {
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const isDark = variant === "dark";

  // Close any open row menu when clicking elsewhere.
  useEffect(() => {
    if (!menuOpenId && !confirmDeleteId) return;
    const close = () => {
      setMenuOpenId(null);
      setConfirmDeleteId(null);
    };
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [menuOpenId, confirmDeleteId]);

  useEffect(() => {
    if (editingId) inputRef.current?.focus();
  }, [editingId]);

  const startRename = (conv: Conversation) => {
    setMenuOpenId(null);
    setEditingId(conv.id);
    setEditValue(conv.title);
  };

  const commitRename = () => {
    if (editingId && editValue.trim()) {
      onRenameConversation?.(editingId, editValue.trim());
    }
    setEditingId(null);
  };

  const hasActions = Boolean(onRenameConversation || onDeleteConversation);

  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={onCreateNewConversation}
        className={cn(
          "flex items-center gap-2 w-full px-3 py-2 rounded-xl",
          "text-sm transition-all duration-150 cursor-pointer mb-1",
          isDark
            ? "text-cream/60 hover:text-cream hover:bg-white/8"
            : "text-warm-gray hover:text-charcoal hover:bg-cream-dark",
        )}
      >
        <Plus size={14} strokeWidth={2.5} />
        <span>New thread</span>
      </button>

      {conversations.map((conv) => {
        const isActive = conv.id === selectedId;
        const isEditing = editingId === conv.id;

        if (isEditing) {
          return (
            <div
              key={conv.id}
              className={cn(
                "flex items-center gap-1 px-1.5 py-1 rounded-xl",
                isDark ? "bg-white/12" : "bg-cream-dark",
              )}
            >
              <input
                ref={inputRef}
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitRename();
                  if (e.key === "Escape") setEditingId(null);
                }}
                className={cn(
                  "flex-1 min-w-0 bg-transparent px-1.5 py-1 text-sm rounded-lg",
                  "focus:outline-none",
                  isDark
                    ? "text-cream placeholder:text-cream/40"
                    : "text-charcoal placeholder:text-warm-gray/50",
                )}
              />
              <button
                onClick={commitRename}
                className={cn(
                  "w-6 h-6 rounded-lg flex items-center justify-center shrink-0 cursor-pointer transition-colors",
                  isDark
                    ? "text-cream/60 hover:text-cream hover:bg-white/10"
                    : "text-warm-gray hover:text-charcoal hover:bg-sand-light",
                )}
              >
                <Check size={14} />
              </button>
              <button
                onClick={() => setEditingId(null)}
                className={cn(
                  "w-6 h-6 rounded-lg flex items-center justify-center shrink-0 cursor-pointer transition-colors",
                  isDark
                    ? "text-cream/60 hover:text-cream hover:bg-white/10"
                    : "text-warm-gray hover:text-charcoal hover:bg-sand-light",
                )}
              >
                <X size={14} />
              </button>
            </div>
          );
        }

        return (
          <div key={conv.id} className="group relative flex items-center">
            <button
              onClick={() => onSelectConversation(conv)}
              className={cn(
                "flex-1 min-w-0 px-3 py-2 rounded-xl text-left",
                "text-sm truncate transition-all duration-150 cursor-pointer",
                hasActions && "pr-8",
                isDark
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

            {hasActions && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmDeleteId(null);
                  setMenuOpenId((prev) => (prev === conv.id ? null : conv.id));
                }}
                className={cn(
                  "absolute right-1.5 w-6 h-6 rounded-lg flex items-center justify-center cursor-pointer transition-all",
                  "opacity-0 group-hover:opacity-100 focus:opacity-100",
                  menuOpenId === conv.id && "opacity-100",
                  isDark
                    ? "text-cream/50 hover:text-cream hover:bg-white/10"
                    : "text-warm-gray hover:text-charcoal hover:bg-sand-light",
                )}
              >
                <MoreHorizontal size={15} />
              </button>
            )}

            {menuOpenId === conv.id && (
              <div
                onClick={(e) => e.stopPropagation()}
                className={cn(
                  "absolute right-1.5 top-9 z-20 w-36 rounded-xl p-1 shadow-lg",
                  isDark
                    ? "bg-sidebar-bg border border-white/10"
                    : "bg-warm-white border border-sand-light",
                )}
              >
                {onRenameConversation && (
                  <button
                    onClick={() => startRename(conv)}
                    className={cn(
                      "flex items-center gap-2 w-full px-2.5 py-1.5 rounded-lg text-sm cursor-pointer transition-colors",
                      isDark
                        ? "text-cream/70 hover:text-cream hover:bg-white/10"
                        : "text-warm-gray hover:text-charcoal hover:bg-cream-dark",
                    )}
                  >
                    <Pencil size={13} />
                    <span>Rename</span>
                  </button>
                )}
                {onDeleteConversation && (
                  <button
                    onClick={() => {
                      if (confirmDeleteId === conv.id) {
                        onDeleteConversation(conv.id);
                        setMenuOpenId(null);
                        setConfirmDeleteId(null);
                      } else {
                        setConfirmDeleteId(conv.id);
                      }
                    }}
                    className={cn(
                      "flex items-center gap-2 w-full px-2.5 py-1.5 rounded-lg text-sm cursor-pointer transition-colors",
                      "text-red-400 hover:bg-red-500/10",
                    )}
                  >
                    <Trash2 size={13} />
                    <span>
                      {confirmDeleteId === conv.id ? "Confirm delete" : "Delete"}
                    </span>
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
