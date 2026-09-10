import { Link } from "react-router-dom";
import {
  Clock,
  LogOut,
  PanelLeftClose,
  Shield,
  ListTree,
  X,
} from "lucide-react";
import { ConversationList } from "./ConversationList";
import type { Conversation } from "../hooks/useConversations";
import catIcon from "../assets/cat.png";

type SidebarContentProps = {
  conversations: Conversation[];
  onCreateNewConversation: () => void;
  onSelectConversation: (conversation: Conversation) => void;
  onRenameConversation: (id: string, title: string) => void;
  onDeleteConversation: (id: string) => void;
  selectedId?: string;
  isAdmin: boolean;
  onShowAdmin: () => void;
  onShowScheduler: () => void;
  onLogout: () => void;
  /** Desktop: collapse the sidebar. Renders a PanelLeftClose button. */
  onCollapse?: () => void;
  /** Mobile: close the drawer. Renders an X button. */
  onCloseDrawer?: () => void;
};

/**
 * The dark sidebar body shared by the desktop sidebar and the mobile drawer.
 * Shows the recent conversations, a link to the full list, and admin/account
 * actions. Exactly one of `onCollapse`/`onCloseDrawer` is expected per usage.
 */
export const SidebarContent = ({
  conversations,
  onCreateNewConversation,
  onSelectConversation,
  onRenameConversation,
  onDeleteConversation,
  selectedId,
  isAdmin,
  onShowAdmin,
  onShowScheduler,
  onLogout,
  onCollapse,
  onCloseDrawer,
}: SidebarContentProps) => {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-white/8">
        <div className="flex items-center gap-2.5">
          <img src={catIcon} alt="Simba" className="w-12 h-12" />
          <h2
            className="text-lg font-bold text-cream tracking-tight"
            style={{ fontFamily: "var(--font-display)" }}
          >
            asksimba
          </h2>
        </div>
        {onCollapse && (
          <button
            onClick={onCollapse}
            className="w-7 h-7 rounded-lg flex items-center justify-center text-cream/40 hover:text-cream hover:bg-white/10 transition-all cursor-pointer"
          >
            <PanelLeftClose size={15} />
          </button>
        )}
        {onCloseDrawer && (
          <button
            onClick={onCloseDrawer}
            className="w-7 h-7 rounded-lg flex items-center justify-center text-cream/40 hover:text-cream hover:bg-white/10 transition-all cursor-pointer"
          >
            <X size={16} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3">
        <ConversationList
          conversations={conversations}
          onCreateNewConversation={onCreateNewConversation}
          onSelectConversation={onSelectConversation}
          onRenameConversation={onRenameConversation}
          onDeleteConversation={onDeleteConversation}
          selectedId={selectedId}
        />
      </div>

      <div className="px-2 pb-3 pt-2 border-t border-white/8 flex flex-col gap-0.5">
        <Link
          to="/conversations"
          onClick={onCloseDrawer}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
        >
          <ListTree size={14} />
          <span>See all conversations</span>
        </Link>
        {isAdmin && (
          <>
            <button
              onClick={onShowAdmin}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
            >
              <Shield size={14} />
              <span>Admin</span>
            </button>
            <button
              onClick={onShowScheduler}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
            >
              <Clock size={14} />
              <span>Scheduler</span>
            </button>
          </>
        )}
        <button
          onClick={onLogout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-cream/50 hover:text-cream hover:bg-white/8 transition-all cursor-pointer"
        >
          <LogOut size={14} />
          <span>Sign out</span>
        </button>
      </div>
    </div>
  );
};
