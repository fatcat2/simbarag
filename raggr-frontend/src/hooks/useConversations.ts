import { useState, useCallback, useEffect } from "react";
import { conversationService } from "../api/conversationService";

export type Conversation = {
  title: string;
  id: string;
};

type Message = {
  text: string;
  speaker: "simba" | "user" | "tool";
  image_key?: string | null;
};

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);

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

  const selectConversation = useCallback(
    async (conversation: Conversation): Promise<Message[]> => {
      setSelectedConversation(conversation);
      try {
        const fetched = await conversationService.getConversation(
          conversation.id,
        );
        return fetched.messages.map((m) => ({
          text: m.text,
          speaker: m.speaker,
          image_key: m.image_key,
        }));
      } catch (err) {
        console.error("Failed to load messages:", err);
        return [];
      }
    },
    [],
  );

  const createConversation = useCallback(async (): Promise<Conversation> => {
    const newConv = await conversationService.createConversation();
    const conversation = { title: newConv.name, id: newConv.id };
    setConversations((prev) => [conversation, ...prev]);
    setSelectedConversation(conversation);
    return conversation;
  }, []);

  return {
    conversations,
    selectedConversation,
    setSelectedConversation,
    selectConversation,
    createConversation,
    refreshConversations,
  };
}
