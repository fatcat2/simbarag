import { useEffect, useState, useRef } from "react";

type MessageInputProps = {
  handleQueryChange: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleKeyDown: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleQuestionSubmit: () => void;
  setSimbaMode: (sdf: boolean) => void;
  query: string;
  isLoading: boolean;
};

export const MessageInput = ({
  query,
  handleKeyDown,
  handleQueryChange,
  handleQuestionSubmit,
  setSimbaMode,
  isLoading,
}: MessageInputProps) => {
  return (
    <div className="flex flex-col gap-4 sticky bottom-0 bg-[#3D763A] p-6 rounded-xl">
      <div className="flex flex-row justify-between grow">
        <textarea
          className="p-3 sm:p-4 border border-blue-200 rounded-md grow bg-[#F9F5EB] min-h-[44px] resize-y"
          onChange={handleQueryChange}
          onKeyDown={handleKeyDown}
          value={query}
          rows={2}
          placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
        />
      </div>
      <div className="flex flex-row justify-between gap-2 grow">
        <button
          className={`p-3 sm:p-4 min-h-[44px] border border-blue-400 rounded-md flex-grow text-sm sm:text-base ${
            isLoading
              ? "bg-gray-400 cursor-not-allowed opacity-50"
              : "bg-[#EDA541] hover:bg-blue-400 cursor-pointer"
          }`}
          onClick={() => handleQuestionSubmit()}
          type="submit"
          disabled={isLoading}
        >
          {isLoading ? "Sending..." : "Submit"}
        </button>
      </div>
      <div className="flex flex-row justify-center gap-2 grow items-center">
        <input
          type="checkbox"
          onChange={(event) => setSimbaMode(event.target.checked)}
          className="w-5 h-5 cursor-pointer"
        />
        <p className="text-sm sm:text-base">simba mode?</p>
      </div>
    </div>
  );
};
