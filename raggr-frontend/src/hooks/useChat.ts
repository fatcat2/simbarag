import { useState, useCallback, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
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
  createConversation: () => Promise<Conversation>;
  refreshConversations: () => Promise<void>;
  onSessionExpired: () => void;
  scrollToBottom: () => void;
};

export function useChat({
  createConversation,
  refreshConversations,
  onSessionExpired,
  scrollToBottom,
}: UseChatOptions) {
  const { conversationId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [pendingImage, setPendingImage] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);

  const isMountedRef = useRef(true);
  // True once tokens for the current assistant reply have started arriving, so
  // new content appends to the live bubble instead of creating another one.
  const streamingActiveRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Set to a conversation id we just created locally, so the route-change
  // loader below doesn't wipe the optimistic message + in-flight stream.
  const skipLoadForIdRef = useRef<string | null>(null);

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

  // Load messages whenever the active conversation (URL) changes. Clearing
  // immediately makes the switch feel instant instead of lingering on the old
  // thread until the fetch resolves.
  useEffect(() => {
    // Skip only for a conversation we just created locally (its optimistic
    // message + stream are already in state). Guard against the null sentinel
    // colliding with the "no conversation" (home) route.
    if (
      skipLoadForIdRef.current !== null &&
      skipLoadForIdRef.current === conversationId
    ) {
      skipLoadForIdRef.current = null;
      return;
    }
    if (!conversationId) {
      setMessages([]);
      setMessagesLoading(false);
      return;
    }
    let cancelled = false;
    setMessages([]);
    setMessagesLoading(true);
    (async () => {
      try {
        const fetched = await conversationService.getConversation(conversationId);
        if (cancelled) return;
        setMessages(
          (fetched.messages ?? []).map((m) => ({
            text: m.text,
            speaker: m.speaker,
            image_key: m.image_key,
          })),
        );
        scrollToBottom();
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load messages:", err);
          setMessages([]);
        }
      } finally {
        if (!cancelled) setMessagesLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId, scrollToBottom]);

  const sendMessage = useCallback(
    async (query: string, simbaMode: boolean) => {
      if ((!query.trim() && !pendingImage) || isLoading) return;

      let activeId = conversationId;
      const createdNew = !activeId;
      if (!activeId) {
        const created = await createConversation();
        // Prevent the route-change loader from clearing what we're about to add.
        skipLoadForIdRef.current = created.id;
        activeId = created.id;
      }

      const imageFile = pendingImage;

      setError(null);
      streamingActiveRef.current = false;
      setStreaming(false);
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
            activeId,
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
          activeId,
          (event) => {
            if (!isMountedRef.current) return;
            if (event.type === "tool_start") {
              // Any text after a tool call belongs in a fresh bubble.
              streamingActiveRef.current = false;
              const friendly =
                TOOL_MESSAGES[event.tool] ?? `Using ${event.tool}...`;
              updateMessages((prev) =>
                prev.concat([{ text: friendly, speaker: "tool" }]),
              );
            } else if (event.type === "content") {
              if (streamingActiveRef.current) {
                updateMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  updated[updated.length - 1] = {
                    ...last,
                    text: last.text + event.delta,
                  };
                  return updated;
                });
              } else {
                streamingActiveRef.current = true;
                setStreaming(true);
                updateMessages((prev) =>
                  prev.concat([{ text: event.delta, speaker: "simba" }]),
                );
              }
            } else if (event.type === "response") {
              // Reconcile the streamed bubble with the authoritative (persisted)
              // text; if nothing streamed, append it as a new message.
              if (streamingActiveRef.current) {
                updateMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    text: event.message,
                  };
                  return updated;
                });
                streamingActiveRef.current = false;
              } else {
                updateMessages((prev) =>
                  prev.concat([{ text: event.message, speaker: "simba" }]),
                );
              }
            } else if (event.type === "error") {
              console.error("Stream error:", event.message);
              if (isMountedRef.current) {
                setError("Simba ran into a problem answering that.");
              }
            }
          },
          abortController.signal,
          imageKey,
        );
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          // User cancelled — not an error to surface.
        } else {
          console.error("Failed to send query:", err);
          if (
            err instanceof Error &&
            err.message.includes("Session expired")
          ) {
            onSessionExpired();
          } else if (isMountedRef.current) {
            setError("Couldn't reach Simba. Check your connection and try again.");
          }
        }
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
          setStreaming(false);
          if (createdNew) {
            refreshConversations();
          }
        }
        streamingActiveRef.current = false;
        abortControllerRef.current = null;
      }
    },
    [
      pendingImage,
      isLoading,
      conversationId,
      createConversation,
      refreshConversations,
      onSessionExpired,
      updateMessages,
    ],
  );

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    setMessages: updateMessages,
    isLoading,
    streaming,
    messagesLoading,
    pendingImage,
    setPendingImage,
    sendMessage,
    stopGeneration,
    error,
    clearError,
  };
}
