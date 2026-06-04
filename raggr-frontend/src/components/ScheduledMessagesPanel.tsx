import { useState } from "react";
import { X, Clock, Send, Trash2, XCircle, RotateCcw } from "lucide-react";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { useScheduledMessages } from "../hooks/useScheduledMessages";
import {
  scheduledMessageService,
  type CreateScheduledMessage,
} from "../api/scheduledMessageService";

type Props = {
  onClose: () => void;
};

const STATUS_BADGE: Record<string, "amber" | "default" | "destructive" | "muted"> = {
  pending: "amber",
  sent: "default",
  failed: "destructive",
  cancelled: "muted",
};

export const ScheduledMessagesPanel = ({ onClose }: Props) => {
  const { messages, loading, refresh } = useScheduledMessages();
  const [channel, setChannel] = useState<"imessage" | "email">("imessage");
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async () => {
    setError("");
    if (!recipient || !content || !scheduledAt) {
      setError("Recipient, content, and scheduled time are required.");
      return;
    }
    if (channel === "email" && !subject) {
      setError("Subject is required for email.");
      return;
    }

    setSubmitting(true);
    try {
      const data: CreateScheduledMessage = {
        recipient,
        channel,
        content,
        scheduled_at: new Date(scheduledAt).toISOString(),
      };
      if (channel === "email") data.subject = subject;
      await scheduledMessageService.create(data);
      setRecipient("");
      setSubject("");
      setContent("");
      setScheduledAt("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to schedule message");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await scheduledMessageService.update(id, { status: "cancelled" });
      refresh();
    } catch {}
  };

  const handleDelete = async (id: string) => {
    try {
      await scheduledMessageService.remove(id);
      refresh();
    } catch {}
  };

  const handleRetry = async (id: string) => {
    try {
      const futureTime = new Date(Date.now() + 30_000).toISOString();
      await scheduledMessageService.update(id, { scheduled_at: futureTime });
      refresh();
    } catch {}
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className={cn(
          "bg-warm-white rounded-3xl shadow-2xl shadow-charcoal/20",
          "w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col",
          "border border-sand-light/60",
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-sand-light/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-pale flex items-center justify-center">
              <Clock size={14} className="text-amber-glow" />
            </div>
            <h2 className="text-sm font-semibold text-charcoal">
              Scheduled Messages
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-colors cursor-pointer"
          >
            <X size={15} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 rounded-b-3xl">
          {/* Create form */}
          <div className="px-6 py-5 border-b border-sand-light/60 space-y-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setChannel("imessage")}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                  channel === "imessage"
                    ? "bg-leaf-pale text-leaf-dark"
                    : "bg-sand-light/40 text-warm-gray hover:text-charcoal",
                )}
              >
                iMessage
              </button>
              <button
                onClick={() => setChannel("email")}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer",
                  channel === "email"
                    ? "bg-leaf-pale text-leaf-dark"
                    : "bg-sand-light/40 text-warm-gray hover:text-charcoal",
                )}
              >
                Email
              </button>
            </div>

            <div className="flex gap-2">
              <Input
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder={channel === "imessage" ? "+15551234567" : "user@example.com"}
                className="flex-1"
              />
              <Input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="w-52"
              />
            </div>

            {channel === "email" && (
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Subject"
              />
            )}

            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Message content..."
              rows={3}
              className="w-full rounded-xl border border-sand bg-cream-light px-3 py-2 text-sm text-charcoal placeholder:text-warm-gray/50 focus:outline-none focus:ring-2 focus:ring-leaf/30 resize-none"
            />

            {error && <p className="text-xs text-red-500">{error}</p>}

            <Button onClick={handleCreate} disabled={submitting} size="sm">
              <Send size={12} />
              {submitting ? "Scheduling..." : "Schedule"}
            </Button>
          </div>

          {/* Message list */}
          {loading ? (
            <div className="px-6 py-12 text-center text-warm-gray text-sm">
              <div className="flex justify-center gap-1.5 mb-3">
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
              </div>
              Loading...
            </div>
          ) : messages.length === 0 ? (
            <div className="px-6 py-12 text-center text-warm-gray text-sm">
              No scheduled messages yet.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Channel</TableHead>
                  <TableHead>Recipient</TableHead>
                  <TableHead>Content</TableHead>
                  <TableHead>Scheduled</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-28">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {messages.map((msg) => (
                  <TableRow key={msg.id}>
                    <TableCell className="capitalize text-xs">
                      {msg.channel}
                    </TableCell>
                    <TableCell className="text-xs truncate max-w-[140px]" title={msg.recipient}>
                      {msg.recipient}
                    </TableCell>
                    <TableCell className="text-xs truncate max-w-[180px]" title={msg.content}>
                      {msg.content.length > 60
                        ? msg.content.slice(0, 60) + "..."
                        : msg.content}
                    </TableCell>
                    <TableCell className="text-xs text-warm-gray">
                      {new Date(msg.scheduled_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_BADGE[msg.status]}>{msg.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {msg.status === "pending" && (
                          <Button
                            size="sm"
                            variant="ghost-dark"
                            onClick={() => handleCancel(msg.id)}
                            title="Cancel"
                          >
                            <XCircle size={11} />
                          </Button>
                        )}
                        {msg.status === "failed" && (
                          <Button
                            size="sm"
                            variant="ghost-dark"
                            onClick={() => handleRetry(msg.id)}
                            title="Retry"
                          >
                            <RotateCcw size={11} />
                          </Button>
                        )}
                        {(msg.status === "pending" || msg.status === "cancelled") && (
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDelete(msg.id)}
                            title="Delete"
                          >
                            <Trash2 size={11} />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </div>
    </div>
  );
};
