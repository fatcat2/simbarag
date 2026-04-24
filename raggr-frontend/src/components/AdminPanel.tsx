import { useState } from "react";
import { X, Phone, PhoneOff, Pencil, Check, Mail, Copy } from "lucide-react";
import { userService, type AdminUserRecord } from "../api/userService";
import { cn } from "../lib/utils";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { useAdminUsers } from "../hooks/useAdminUsers";

type Props = {
  onClose: () => void;
};

export const AdminPanel = ({ onClose }: Props) => {
  const { users, loading, updateUser } = useAdminUsers();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [rowError, setRowError] = useState<Record<string, string>>({});
  const [rowSuccess, setRowSuccess] = useState<Record<string, string>>({});

  const startEdit = (user: AdminUserRecord) => {
    setEditingId(user.id);
    setEditValue(user.whatsapp_number ?? "");
    setRowError((p) => ({ ...p, [user.id]: "" }));
    setRowSuccess((p) => ({ ...p, [user.id]: "" }));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const saveWhatsapp = async (userId: string) => {
    setRowError((p) => ({ ...p, [userId]: "" }));
    try {
      const updated = await userService.adminSetWhatsapp(userId, editValue);
      updateUser(userId, () => updated);
      setRowSuccess((p) => ({ ...p, [userId]: "Saved" }));
      setEditingId(null);
      setTimeout(() => setRowSuccess((p) => ({ ...p, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((p) => ({
        ...p,
        [userId]: err instanceof Error ? err.message : "Failed to save",
      }));
    }
  };

  const unlinkWhatsapp = async (userId: string) => {
    setRowError((p) => ({ ...p, [userId]: "" }));
    try {
      await userService.adminUnlinkWhatsapp(userId);
      updateUser(userId, (u) => ({ ...u, whatsapp_number: null }));
      setRowSuccess((p) => ({ ...p, [userId]: "Unlinked" }));
      setTimeout(() => setRowSuccess((p) => ({ ...p, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((p) => ({
        ...p,
        [userId]: err instanceof Error ? err.message : "Failed to unlink",
      }));
    }
  };

  const toggleEmail = async (userId: string) => {
    setRowError((p) => ({ ...p, [userId]: "" }));
    try {
      const updated = await userService.adminToggleEmail(userId);
      updateUser(userId, () => updated);
      setRowSuccess((p) => ({ ...p, [userId]: "Email enabled" }));
      setTimeout(() => setRowSuccess((p) => ({ ...p, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((p) => ({
        ...p,
        [userId]: err instanceof Error ? err.message : "Failed to enable email",
      }));
    }
  };

  const disableEmail = async (userId: string) => {
    setRowError((p) => ({ ...p, [userId]: "" }));
    try {
      await userService.adminDisableEmail(userId);
      updateUser(userId, (u) => ({ ...u, email_enabled: false, email_address: null }));
      setRowSuccess((p) => ({ ...p, [userId]: "Email disabled" }));
      setTimeout(() => setRowSuccess((p) => ({ ...p, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((p) => ({
        ...p,
        [userId]: err instanceof Error ? err.message : "Failed to disable email",
      }));
    }
  };

  const copyToClipboard = (text: string, userId: string) => {
    navigator.clipboard.writeText(text);
    setRowSuccess((p) => ({ ...p, [userId]: "Copied" }));
    setTimeout(() => setRowSuccess((p) => ({ ...p, [userId]: "" })), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/40 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className={cn(
          "bg-warm-white rounded-3xl shadow-2xl shadow-charcoal/20",
          "w-full max-w-3xl mx-4 max-h-[82vh] flex flex-col",
          "border border-sand-light/60",
        )}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-sand-light/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-leaf-pale flex items-center justify-center">
              <Phone size={14} className="text-leaf-dark" />
            </div>
            <h2 className="text-sm font-semibold text-charcoal">
              Admin · User Integrations
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
          {loading ? (
            <div className="px-6 py-12 text-center text-warm-gray text-sm">
              <div className="flex justify-center gap-1.5 mb-3">
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
                <span className="loading-dot w-2 h-2 rounded-full bg-amber-soft inline-block" />
              </div>
              Loading users...
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>WhatsApp</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className="w-28">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium text-charcoal">
                      {user.username}
                    </TableCell>
                    <TableCell className="text-warm-gray">{user.email}</TableCell>
                    <TableCell>
                      {editingId === user.id ? (
                        <div className="flex flex-col gap-1">
                          <Input
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            placeholder="whatsapp:+15551234567"
                            className="w-52"
                            autoFocus
                            onKeyDown={(e) =>
                              e.key === "Enter" && saveWhatsapp(user.id)
                            }
                          />
                          {rowError[user.id] && (
                            <span className="text-xs text-red-500">
                              {rowError[user.id]}
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className="flex flex-col gap-0.5">
                          <span
                            className={cn(
                              "text-sm",
                              user.whatsapp_number
                                ? "text-charcoal"
                                : "text-warm-gray/40 italic",
                            )}
                          >
                            {user.whatsapp_number ?? "\u2014"}
                          </span>
                          {rowSuccess[user.id] && (
                            <span className="text-xs text-leaf-dark">
                              {rowSuccess[user.id]}
                            </span>
                          )}
                          {rowError[user.id] && (
                            <span className="text-xs text-red-500">
                              {rowError[user.id]}
                            </span>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-0.5">
                        {user.email_enabled && user.email_address ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm text-charcoal truncate max-w-[180px]" title={user.email_address}>
                              {user.email_address}
                            </span>
                            <button
                              onClick={() => copyToClipboard(user.email_address!, user.id)}
                              className="text-warm-gray hover:text-charcoal transition-colors cursor-pointer"
                              title="Copy address"
                            >
                              <Copy size={11} />
                            </button>
                          </div>
                        ) : (
                          <span className="text-sm text-warm-gray/40 italic">\u2014</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {editingId === user.id ? (
                        <div className="flex gap-1.5">
                          <Button
                            size="sm"
                            variant="default"
                            onClick={() => saveWhatsapp(user.id)}
                          >
                            <Check size={12} />
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost-dark"
                            onClick={cancelEdit}
                          >
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <div className="flex gap-1.5">
                          <Button
                            size="sm"
                            variant="ghost-dark"
                            onClick={() => startEdit(user)}
                          >
                            <Pencil size={11} />
                            Edit
                          </Button>
                          {user.whatsapp_number && (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => unlinkWhatsapp(user.id)}
                            >
                              <PhoneOff size={11} />
                              Unlink
                            </Button>
                          )}
                          {user.email_enabled ? (
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => disableEmail(user.id)}
                            >
                              <Mail size={11} />
                              Email
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="ghost-dark"
                              onClick={() => toggleEmail(user.id)}
                            >
                              <Mail size={11} />
                              Email
                            </Button>
                          )}
                        </div>
                      )}
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
