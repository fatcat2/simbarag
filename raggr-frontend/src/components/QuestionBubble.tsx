import React from "react";
import { cn } from "../lib/utils";
import { usePresignedUrl } from "../hooks/usePresignedUrl";

type QuestionBubbleProps = {
  text: string;
  image_key?: string | null;
};

export const QuestionBubble = React.memo(({ text, image_key }: QuestionBubbleProps) => {
  const { imageUrl, imageError } = usePresignedUrl(image_key);

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
        {imageError && (
          <div className="flex items-center gap-2 text-xs text-charcoal/50 bg-charcoal/5 rounded-xl px-3 py-2 mb-2">
            <span>Image failed to load</span>
          </div>
        )}
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
});
