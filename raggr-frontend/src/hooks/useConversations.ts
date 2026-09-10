import { useState, useCallback, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { conversationService } from "../api/conversationService";

export type Conversation = {
  title: string;
  id: string;
};

export function useConversations() {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const refreshConversations = useCallback(async () => {
    try {
      const fetched = await conversationService.getAllConversations();
      setConversations(fetched.map((c) => ({ id: c.id, title: c.name })));
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // The active conversation is derived from the URL. Fall back to a minimal
  // object while the list is still loading (e.g. on a deep-link refresh).
  const selectedConversation = useMemo<Conversation | null>(() => {
    if (!conversationId) return null;
    return (
      conversations.find((c) => c.id === conversationId) ?? {
        id: conversationId,
        title: "",
      }
    );
  }, [conversationId, conversations]);

  const createConversation = useCallback(async (): Promise<Conversation> => {
    const newConv = await conversationService.createConversation();
    const conversation = { title: newConv.name, id: newConv.id };
    setConversations((prev) => [conversation, ...prev]);
    navigate(`/c/${conversation.id}`);
    return conversation;
  }, [navigate]);

  const renameConversation = useCallback(
    async (id: string, title: string): Promise<void> => {
      const trimmed = title.trim();
      if (!trimmed) return;
      // Optimistic update, roll back on failure. selectedConversation is
      // derived from `conversations`, so it updates automatically.
      const previous = conversations;
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title: trimmed } : c)),
      );
      try {
        await conversationService.renameConversation(id, trimmed);
      } catch (err) {
        console.error("Failed to rename conversation:", err);
        setConversations(previous);
      }
    },
    [conversations],
  );

  const deleteConversation = useCallback(
    async (id: string): Promise<void> => {
      const previous = conversations;
      const wasActive = conversationId === id;
      setConversations((prev) => prev.filter((c) => c.id !== id));
      // Navigating home clears the message view via the route change.
      if (wasActive) navigate("/");
      try {
        await conversationService.deleteConversation(id);
      } catch (err) {
        console.error("Failed to delete conversation:", err);
        setConversations(previous);
      }
    },
    [conversations, conversationId, navigate],
  );

  return {
    conversations,
    selectedConversation,
    createConversation,
    renameConversation,
    deleteConversation,
    refreshConversations,
  };
}
