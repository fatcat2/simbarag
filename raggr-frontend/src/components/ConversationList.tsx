import { useState, useEffect } from "react";

import { conversationService } from "../api/conversationService";
type Conversation = {
  title: string;
  id: string;
};

type ConversationProps = {
  conversations: Conversation[];
  onSelectConversation: (conversation: Conversation) => void;
  onCreateNewConversation: () => void;
};

export const ConversationList = ({
  conversations,
  onSelectConversation,
  onCreateNewConversation,
}: ConversationProps) => {
  const [conservations, setConversations] = useState(conversations);

  useEffect(() => {
    const loadConversations = async () => {
      try {
        const fetchedConversations =
          await conversationService.getAllConversations();
        setConversations(
          fetchedConversations.map((conversation) => ({
            id: conversation.id,
            title: conversation.name,
          })),
        );
      } catch (error) {
        console.error("Failed to load messages:", error);
      }
    };
    loadConversations();
  }, []);

  return (
    <div className="bg-indigo-300 rounded-md p-3 sm:p-4 flex flex-col gap-1">
      {conservations.map((conversation) => {
        return (
          <div
            key={conversation.id}
            className="border-blue-400 bg-indigo-300 hover:bg-indigo-200 cursor-pointer rounded-md p-3 min-h-[44px] flex items-center"
            onClick={() => onSelectConversation(conversation)}
          >
            <p className="text-sm sm:text-base break-words">
              {conversation.title}
            </p>
          </div>
        );
      })}
      <div
        className="border-blue-400 bg-indigo-300 hover:bg-indigo-200 cursor-pointer rounded-md p-3 min-h-[44px] flex items-center"
        onClick={() => onCreateNewConversation()}
      >
        <p className="text-sm sm:text-base"> + Start a new thread</p>
      </div>
    </div>
  );
};
