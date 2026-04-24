import { useState, useEffect } from "react";
import { userService, type AdminUserRecord } from "../api/userService";

export function useAdminUsers() {
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    userService
      .adminListUsers()
      .then(setUsers)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const updateUser = (userId: string, updater: (u: AdminUserRecord) => AdminUserRecord) => {
    setUsers((prev) => prev.map((u) => (u.id === userId ? updater(u) : u)));
  };

  return { users, loading, updateUser };
}
