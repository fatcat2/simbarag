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
    <div className="bg-indigo-300 rounded-md p-3 flex flex-col">
      {conservations.map((conversation) => {
        return (
          <div
            className="border-blue-400 bg-indigo-300 hover:bg-indigo-200 cursor-pointer rounded-md p-2"
            onClick={() => onSelectConversation(conversation)}
          >
            <p>{conversation.title}</p>
          </div>
        );
      })}
      <div
        className="border-blue-400 bg-indigo-300 hover:bg-indigo-200 cursor-pointer rounded-md p-2"
        onClick={() => onCreateNewConversation()}
      >
        <p> + Start a new thread</p>
      </div>
    </div>
  );
};
