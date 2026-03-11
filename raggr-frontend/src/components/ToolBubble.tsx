import { cn } from "../lib/utils";

export const ToolBubble = ({ text }: { text: string }) => (
  <div className="flex justify-center message-enter">
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full",
        "bg-leaf-pale border border-leaf-light/50",
        "text-xs text-leaf-dark italic",
      )}
    >
      {text}
    </div>
  </div>
);
