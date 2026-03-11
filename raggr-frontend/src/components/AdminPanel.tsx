import { useEffect, useState } from "react";
import { userService, type AdminUserRecord } from "../api/userService";

type Props = {
  onClose: () => void;
};

export const AdminPanel = ({ onClose }: Props) => {
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [rowError, setRowError] = useState<Record<string, string>>({});
  const [rowSuccess, setRowSuccess] = useState<Record<string, string>>({});

  useEffect(() => {
    userService
      .adminListUsers()
      .then(setUsers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const startEdit = (user: AdminUserRecord) => {
    setEditingId(user.id);
    setEditValue(user.whatsapp_number ?? "");
    setRowError((prev) => ({ ...prev, [user.id]: "" }));
    setRowSuccess((prev) => ({ ...prev, [user.id]: "" }));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const saveWhatsapp = async (userId: string) => {
    setRowError((prev) => ({ ...prev, [userId]: "" }));
    try {
      const updated = await userService.adminSetWhatsapp(userId, editValue);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
      setRowSuccess((prev) => ({ ...prev, [userId]: "Saved" }));
      setEditingId(null);
      setTimeout(() => setRowSuccess((prev) => ({ ...prev, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((prev) => ({
        ...prev,
        [userId]: err instanceof Error ? err.message : "Failed to save",
      }));
    }
  };

  const unlinkWhatsapp = async (userId: string) => {
    setRowError((prev) => ({ ...prev, [userId]: "" }));
    try {
      await userService.adminUnlinkWhatsapp(userId);
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, whatsapp_number: null } : u)),
      );
      setRowSuccess((prev) => ({ ...prev, [userId]: "Unlinked" }));
      setTimeout(() => setRowSuccess((prev) => ({ ...prev, [userId]: "" })), 2000);
    } catch (err) {
      setRowError((prev) => ({
        ...prev,
        [userId]: err instanceof Error ? err.message : "Failed to unlink",
      }));
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-warm-white rounded-2xl shadow-2xl w-full max-w-3xl mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-sand-light">
          <h2 className="text-base font-semibold text-charcoal">Admin: WhatsApp Numbers</h2>
          <button
            className="text-warm-gray hover:text-charcoal text-xl leading-none cursor-pointer"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1">
          {loading ? (
            <div className="px-6 py-10 text-center text-warm-gray text-sm">Loading…</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-sand-light text-left text-warm-gray">
                  <th className="px-6 py-3 font-medium">Username</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">WhatsApp</th>
                  <th className="px-6 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-sand-light/50 hover:bg-cream/40 transition-colors"
                  >
                    <td className="px-6 py-3 text-charcoal font-medium">{user.username}</td>
                    <td className="px-6 py-3 text-warm-gray">{user.email}</td>
                    <td className="px-6 py-3">
                      {editingId === user.id ? (
                        <div className="flex flex-col gap-1">
                          <input
                            className="border border-sand-light rounded-lg px-2 py-1 text-sm text-charcoal bg-cream focus:outline-none focus:ring-1 focus:ring-amber-soft w-52"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            placeholder="whatsapp:+15551234567"
                            autoFocus
                          />
                          {rowError[user.id] && (
                            <span className="text-xs text-red-500">{rowError[user.id]}</span>
                          )}
                        </div>
                      ) : (
                        <div className="flex flex-col gap-1">
                          <span className={user.whatsapp_number ? "text-charcoal" : "text-warm-gray/50 italic"}>
                            {user.whatsapp_number ?? "—"}
                          </span>
                          {rowSuccess[user.id] && (
                            <span className="text-xs text-green-600">{rowSuccess[user.id]}</span>
                          )}
                          {rowError[user.id] && (
                            <span className="text-xs text-red-500">{rowError[user.id]}</span>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      {editingId === user.id ? (
                        <div className="flex gap-2">
                          <button
                            className="text-xs px-2.5 py-1 rounded-lg bg-amber-soft/80 text-charcoal hover:bg-amber-soft transition-colors cursor-pointer"
                            onClick={() => saveWhatsapp(user.id)}
                          >
                            Save
                          </button>
                          <button
                            className="text-xs px-2.5 py-1 rounded-lg text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-colors cursor-pointer"
                            onClick={cancelEdit}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            className="text-xs px-2.5 py-1 rounded-lg text-warm-gray hover:text-charcoal hover:bg-cream-dark transition-colors cursor-pointer"
                            onClick={() => startEdit(user)}
                          >
                            Edit
                          </button>
                          {user.whatsapp_number && (
                            <button
                              className="text-xs px-2.5 py-1 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                              onClick={() => unlinkWhatsapp(user.id)}
                            >
                              Unlink
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
