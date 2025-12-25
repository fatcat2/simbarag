type QuestionBubbleProps = {
  text: string;
};

export const QuestionBubble = ({ text }: QuestionBubbleProps) => {
  return (
    <div className="w-2/3 rounded-md bg-stone-200 p-3 sm:p-4 break-words overflow-wrap-anywhere text-sm sm:text-base ml-auto">
      🤦: {text}
    </div>
  );
};
