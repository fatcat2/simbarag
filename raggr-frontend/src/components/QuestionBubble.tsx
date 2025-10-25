type QuestionBubbleProps = {
  text: string;
};

export const QuestionBubble = ({ text }: QuestionBubbleProps) => {
  return <div className="rounded-md bg-stone-200 p-3">🤦: {text}</div>;
};
