import { cn } from "../../lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = ({ className, ...props }: InputProps) => {
  return (
    <input
      className={cn(
        "flex h-8 w-full rounded-lg border border-sand bg-cream px-3 py-1",
        "text-sm text-charcoal placeholder:text-warm-gray/50",
        "focus:outline-none focus:ring-2 focus:ring-amber-soft/60",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
};
