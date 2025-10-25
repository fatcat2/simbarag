type Conversation = {
  title: string;
  id: string;
};

type ConversationMenuProps = {
  conversations: Conversation[];
};

export const ConversationMenu = ({ conversations }: ConversationMenuProps) => {
  return (
    <div className="absolute bg-white w-md rounded-md shadow-xl m-4 p-4">
      <p className="py-2 px-4 rounded-md w-full text-xl font-bold">askSimba!</p>
      {conversations.map((conversation) => (
        <p
          key={conversation.id}
          className="py-2 px-4 rounded-md hover:bg-stone-200 w-full text-xl font-bold cursor-pointer"
        >
          {conversation.title}
        </p>
      ))}
    </div>
  );
};
