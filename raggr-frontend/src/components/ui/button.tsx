import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
  {
    variants: {
      variant: {
        default:
          "bg-leaf text-white shadow-sm shadow-leaf/20 hover:bg-leaf-dark hover:shadow-md hover:shadow-leaf/30 active:scale-[0.97]",
        amber:
          "bg-amber-glow text-white shadow-sm shadow-amber/20 hover:bg-amber-dark hover:shadow-md active:scale-[0.97]",
        ghost:
          "text-cream/70 hover:text-cream hover:bg-white/8 active:scale-[0.97]",
        "ghost-dark":
          "text-warm-gray hover:text-charcoal hover:bg-sand-light/60 active:scale-[0.97]",
        outline:
          "border border-sand bg-transparent text-warm-gray hover:bg-cream-dark hover:text-charcoal active:scale-[0.97]",
        destructive:
          "text-red-400 hover:text-red-600 hover:bg-red-50 active:scale-[0.97]",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-7 px-3 text-xs",
        lg: "h-11 px-6 text-base",
        icon: "h-9 w-9",
        "icon-sm": "h-7 w-7",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = ({ className, variant, size, ...props }: ButtonProps) => {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
};
