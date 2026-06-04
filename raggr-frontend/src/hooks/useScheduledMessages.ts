import { useState, useEffect, useCallback } from "react";
import {
  scheduledMessageService,
  type ScheduledMessage,
} from "../api/scheduledMessageService";

export function useScheduledMessages() {
  const [messages, setMessages] = useState<ScheduledMessage[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    setLoading(true);
    scheduledMessageService
      .list()
      .then(setMessages)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { messages, loading, refresh };
}
