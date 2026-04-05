import React, { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUp, ImagePlus, X } from "lucide-react";
import { cn } from "../lib/utils";
import { Textarea } from "./ui/textarea";

type MessageInputProps = {
  handleQueryChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleKeyDown: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleQuestionSubmit: () => void;
  setSimbaMode: (val: boolean) => void;
  query: string;
  isLoading: boolean;
  pendingImage: File | null;
  onImageSelect: (file: File) => void;
  onClearImage: () => void;
};

export const MessageInput = React.memo(({
  query,
  handleKeyDown,
  handleQueryChange,
  handleQuestionSubmit,
  setSimbaMode,
  isLoading,
  pendingImage,
  onImageSelect,
  onClearImage,
}: MessageInputProps) => {
  const [simbaMode, setLocalSimbaMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Create blob URL once per file, revoke on cleanup
  const previewUrl = useMemo(
    () => (pendingImage ? URL.createObjectURL(pendingImage) : null),
    [pendingImage],
  );

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const toggleSimbaMode = () => {
    const next = !simbaMode;
    setLocalSimbaMode(next);
    setSimbaMode(next);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelect(file);
    }
    // Reset so the same file can be re-selected
    e.target.value = "";
  };

  const canSend = !isLoading && (query.trim() || pendingImage);

  return (
    <div
      className={cn(
        "rounded-2xl bg-warm-white border border-sand shadow-md shadow-sand/30",
        "transition-shadow duration-200 focus-within:shadow-lg focus-within:shadow-amber-soft/20",
        "focus-within:border-amber-soft/60",
      )}
    >
      {/* Image preview */}
      {pendingImage && (
        <div className="px-3 pt-3">
          <div className="relative inline-block">
            <img
              src={previewUrl!}
              alt="Pending upload"
              className="h-20 rounded-lg object-cover border border-sand"
            />
            <button
              type="button"
              onClick={onClearImage}
              className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-charcoal text-white flex items-center justify-center hover:bg-charcoal/80 transition-colors cursor-pointer"
            >
              <X size={12} />
            </button>
          </div>
        </div>
      )}

      {/* Textarea */}
      <Textarea
        onChange={handleQueryChange}
        onKeyDown={handleKeyDown}
        value={query}
        rows={2}
        placeholder="Ask Simba anything..."
        className="min-h-[60px] max-h-40"
      />

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Bottom toolbar */}
      <div className="flex items-center justify-between px-3 pb-2.5 pt-1">
        <div className="flex items-center gap-3">
          {/* Simba mode toggle */}
          <button
            type="button"
            onClick={toggleSimbaMode}
            className="flex items-center gap-2 group cursor-pointer select-none"
          >
            <div className={cn("toggle-track", simbaMode && "checked")}>
              <div className="toggle-thumb" />
            </div>
            <span className="text-xs text-warm-gray group-hover:text-charcoal transition-colors">
              simba mode
            </span>
          </button>

          {/* Image attach button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className={cn(
              "w-7 h-7 rounded-lg flex items-center justify-center transition-all cursor-pointer",
              isLoading
                ? "text-warm-gray/40 cursor-not-allowed"
                : "text-warm-gray hover:text-charcoal hover:bg-cream-dark",
            )}
          >
            <ImagePlus size={16} />
          </button>
        </div>

        {/* Send button */}
        <button
          type="submit"
          onClick={handleQuestionSubmit}
          disabled={!canSend}
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center",
            "transition-all duration-200 cursor-pointer",
            "shadow-sm",
            !canSend
              ? "bg-sand text-warm-gray/50 cursor-not-allowed shadow-none"
              : "bg-amber-glow text-white hover:bg-amber-dark hover:shadow-md hover:shadow-amber-glow/30 active:scale-95",
          )}
        >
          <ArrowUp size={15} strokeWidth={2.5} />
        </button>
      </div>
    </div>
  );
});
