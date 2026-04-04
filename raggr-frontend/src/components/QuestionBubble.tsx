import { cn } from "../lib/utils";
import { conversationService } from "../api/conversationService";

type QuestionBubbleProps = {
  text: string;
  image_key?: string | null;
};

export const QuestionBubble = ({ text, image_key }: QuestionBubbleProps) => {
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
        {image_key && (
          <img
            src={conversationService.getImageUrl(image_key)}
            alt="Uploaded image"
            className="max-w-full rounded-xl mb-2"
          />
        )}
        {text}
      </div>
    </div>
  );
};
