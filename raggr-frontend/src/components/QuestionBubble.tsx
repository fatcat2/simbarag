import { cn } from "../lib/utils";

type QuestionBubbleProps = {
  text: string;
};

export const QuestionBubble = ({ text }: QuestionBubbleProps) => {
  return (
    <div className="flex justify-end message-enter">
      <div
        className={cn(
          "max-w-[72%] rounded-3xl rounded-br-md",
          "bg-leaf-pale border border-leaf-light/60",
          "px-4 py-3 text-sm leading-relaxed text-charcoal",
          "shadow-sm shadow-leaf/10",
        )}
      >
        {text}
      </div>
    </div>
  );
};
