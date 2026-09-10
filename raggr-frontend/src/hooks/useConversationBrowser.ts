import { useCallback, useEffect, useRef, useState } from "react";
import { conversationService } from "../api/conversationService";
import type { Conversation } from "./useConversations";

const PAGE_SIZE = 20;

/**
 * Data source for the dedicated /conversations page: server-side search plus
 * "Load more" pagination. Detects whether more rows exist by asking for one
 * extra item beyond the page size.
 */
export function useConversationBrowser() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [search, setSearchValue] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);

  // Guards against a slow earlier request overwriting a newer one.
  const requestIdRef = useRef(0);

  const fetchPage = useCallback(
    async (offset: number, searchTerm: string) => {
      const requestId = ++requestIdRef.current;
      setLoading(true);
      try {
        const fetched = await conversationService.getAllConversations({
          limit: PAGE_SIZE + 1,
          offset,
          search: searchTerm || undefined,
        });
        if (requestId !== requestIdRef.current) return;

        const page = fetched
          .slice(0, PAGE_SIZE)
          .map((c) => ({ id: c.id, title: c.name }));
        setHasMore(fetched.length > PAGE_SIZE);
        setItems((prev) => (offset === 0 ? page : [...prev, ...page]));
      } catch (err) {
        if (requestId === requestIdRef.current) {
          console.error("Failed to load conversations:", err);
        }
      } finally {
        if (requestId === requestIdRef.current) setLoading(false);
      }
    },
    [],
  );

  // Debounce search changes; reset to the first page on each new term.
  useEffect(() => {
    const handle = setTimeout(() => fetchPage(0, search), 250);
    return () => clearTimeout(handle);
  }, [search, fetchPage]);

  const loadMore = useCallback(() => {
    if (loading || !hasMore) return;
    fetchPage(items.length, search);
  }, [loading, hasMore, items.length, search, fetchPage]);

  const renameConversation = useCallback(
    async (id: string, title: string) => {
      const trimmed = title.trim();
      if (!trimmed) return;
      const previous = items;
      setItems((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: trimmed } : c)),
      );
      try {
        await conversationService.renameConversation(id, trimmed);
      } catch (err) {
        console.error("Failed to rename conversation:", err);
        setItems(previous);
      }
    },
    [items],
  );

  const deleteConversation = useCallback(
    async (id: string) => {
      const previous = items;
      setItems((prev) => prev.filter((c) => c.id !== id));
      try {
        await conversationService.deleteConversation(id);
      } catch (err) {
        console.error("Failed to delete conversation:", err);
        setItems(previous);
      }
    },
    [items],
  );

  return {
    items,
    search,
    setSearch: setSearchValue,
    hasMore,
    loading,
    loadMore,
    renameConversation,
    deleteConversation,
  };
}
