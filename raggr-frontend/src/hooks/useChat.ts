import { useState, useCallback, useEffect, useRef } from "react";
import { conversationService } from "../api/conversationService";
import type { Conversation } from "./useConversations";

type Message = {
  text: string;
  speaker: "simba" | "user" | "tool";
  image_key?: string | null;
};

const TOOL_MESSAGES: Record<string, string> = {
  simba_search: "Searching Simba's records...",
  web_search: "Searching the web...",
  get_current_date: "Checking today's date...",
  ynab_budget_summary: "Checking budget summary...",
  ynab_search_transactions: "Looking up transactions...",
  ynab_category_spending: "Analyzing category spending...",
  ynab_insights: "Generating budget insights...",
  obsidian_search_notes: "Searching notes...",
  obsidian_read_note: "Reading note...",
  obsidian_create_note: "Saving note...",
  obsidian_create_task: "Creating task...",
  journal_get_today: "Reading today's journal...",
  journal_get_tasks: "Getting tasks...",
  journal_add_task: "Adding task...",
  journal_complete_task: "Completing task...",
};

const simbaAnswers = ["meow.", "hiss...", "purrrrrr", "yowOWROWWowowr"];

type UseChatOptions = {
  selectedConversation: Conversation | null;
  createConversation: () => Promise<Conversation>;
  refreshConversations: () => Promise<void>;
  onSessionExpired: () => void;
  scrollToBottom: () => void;
};

export function useChat({
  selectedConversation,
  createConversation,
  refreshConversations,
  onSessionExpired,
  scrollToBottom,
}: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingImage, setPendingImage] = useState<File | null>(null);

  const isMountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const updateMessages = useCallback(
    (updater: Message[] | ((prev: Message[]) => Message[])) => {
      setMessages(updater);
      scrollToBottom();
    },
    [scrollToBottom],
  );

  const sendMessage = useCallback(
    async (query: string, simbaMode: boolean) => {
      if ((!query.trim() && !pendingImage) || isLoading) return;

      let activeConversation = selectedConversation;
      let createdNew = false;
      if (!activeConversation) {
        activeConversation = await createConversation();
        createdNew = true;
      }

      const imageFile = pendingImage;

      updateMessages((prev) => prev.concat([{ text: query, speaker: "user" }]));
      setPendingImage(null);
      setIsLoading(true);

      if (simbaMode) {
        const randomElement =
          simbaAnswers[Math.floor(Math.random() * simbaAnswers.length)];
        updateMessages((prev) =>
          prev.concat([{ text: randomElement, speaker: "simba" }]),
        );
        setIsLoading(false);
        return;
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        let imageKey: string | undefined;
        if (imageFile) {
          const uploadResult = await conversationService.uploadImage(
            imageFile,
            activeConversation.id,
          );
          imageKey = uploadResult.image_key;

          updateMessages((prev) => {
            const updated = [...prev];
            for (let i = updated.length - 1; i >= 0; i--) {
              if (updated[i].speaker === "user") {
                updated[i] = { ...updated[i], image_key: imageKey };
                break;
              }
            }
            return updated;
          });
        }

        await conversationService.streamQuery(
          query,
          activeConversation.id,
          (event) => {
            if (!isMountedRef.current) return;
            if (event.type === "tool_start") {
              const friendly =
                TOOL_MESSAGES[event.tool] ?? `Using ${event.tool}...`;
              updateMessages((prev) =>
                prev.concat([{ text: friendly, speaker: "tool" }]),
              );
            } else if (event.type === "response") {
              updateMessages((prev) =>
                prev.concat([{ text: event.message, speaker: "simba" }]),
              );
            } else if (event.type === "error") {
              console.error("Stream error:", event.message);
            }
          },
          abortController.signal,
          imageKey,
        );
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          console.log("Request was aborted");
        } else {
          console.error("Failed to send query:", error);
          if (
            error instanceof Error &&
            error.message.includes("Session expired")
          ) {
            onSessionExpired();
          }
        }
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
          if (createdNew) {
            refreshConversations();
          }
        }
        abortControllerRef.current = null;
      }
    },
    [
      pendingImage,
      isLoading,
      selectedConversation,
      createConversation,
      refreshConversations,
      onSessionExpired,
      updateMessages,
    ],
  );

  return {
    messages,
    setMessages: updateMessages,
    isLoading,
    pendingImage,
    setPendingImage,
    sendMessage,
  };
}
