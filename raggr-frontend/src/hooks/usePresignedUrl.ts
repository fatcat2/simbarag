import { useState, useEffect } from "react";
import { conversationService } from "../api/conversationService";

const urlCache = new Map<string, string>();

export function usePresignedUrl(imageKey: string | null | undefined) {
  const [imageUrl, setImageUrl] = useState<string | null>(
    imageKey ? (urlCache.get(imageKey) ?? null) : null,
  );
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    if (!imageKey) return;

    const cached = urlCache.get(imageKey);
    if (cached) {
      setImageUrl(cached);
      return;
    }

    conversationService
      .getPresignedImageUrl(imageKey)
      .then((url) => {
        urlCache.set(imageKey, url);
        setImageUrl(url);
      })
      .catch((err) => {
        console.error("Failed to load image:", err);
        setImageError(true);
      });
  }, [imageKey]);

  return { imageUrl, imageError };
}
