import { useEffect, useState } from "react";
import { cn } from "../lib/utils";
import { conversationService } from "../api/conversationService";

type QuestionBubbleProps = {
  text: string;
  image_key?: string | null;
};

export const QuestionBubble = ({ text, image_key }: QuestionBubbleProps) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!image_key) return;
    conversationService.getPresignedImageUrl(image_key).then(setImageUrl).catch(() => {});
  }, [image_key]);

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
        {imageUrl && (
          <img
            src={imageUrl}
            alt="Uploaded image"
            className="max-w-full rounded-xl mb-2"
          />
        )}
        {text}
      </div>
    </div>
  );
};
