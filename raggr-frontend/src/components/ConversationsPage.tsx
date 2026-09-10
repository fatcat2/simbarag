import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Search } from "lucide-react";
import { ConversationList } from "./ConversationList";
import { useConversationBrowser } from "../hooks/useConversationBrowser";
import type { Conversation } from "../hooks/useConversations";
import { Input } from "./ui/input";
import catIcon from "../assets/cat.png";

export const ConversationsPage = () => {
  const navigate = useNavigate();
  const {
    items,
    search,
    setSearch,
    hasMore,
    loading,
    loadMore,
    renameConversation,
    deleteConversation,
  } = useConversationBrowser();

  const handleSelect = useCallback(
    (conversation: Conversation) => navigate(`/c/${conversation.id}`),
    [navigate],
  );

  const handleCreateNew = useCallback(() => navigate("/"), [navigate]);

  return (
    <div className="h-screen h-[100dvh] flex flex-col bg-cream overflow-hidden">
      <header className="flex items-center gap-3 px-4 py-3 bg-warm-white border-b border-sand-light/60">
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 rounded-xl flex items-center justify-center text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-all cursor-pointer"
          aria-label="Back"
        >
          <ArrowLeft size={16} />
        </button>
        <img src={catIcon} alt="Simba" className="w-10 h-10" />
        <h1
          className="text-base font-bold text-charcoal"
          style={{ fontFamily: "var(--font-display)" }}
        >
          All conversations
        </h1>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-4">
          <div className="relative">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-warm-gray/60"
            />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              className="h-10 pl-9"
            />
          </div>

          <div className="bg-warm-white rounded-2xl border border-sand-light p-3 shadow-sm">
            <ConversationList
              conversations={items}
              onCreateNewConversation={handleCreateNew}
              onSelectConversation={handleSelect}
              onRenameConversation={renameConversation}
              onDeleteConversation={deleteConversation}
              variant="light"
            />

            {items.length === 0 && !loading && (
              <p className="text-center text-sm text-warm-gray/70 py-6">
                {search ? "No conversations match your search." : "No conversations yet."}
              </p>
            )}
          </div>

          {hasMore && (
            <button
              onClick={loadMore}
              disabled={loading}
              className="self-center px-4 py-2 rounded-xl text-sm text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Loading..." : "Load more"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
