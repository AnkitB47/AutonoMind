import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type Props = {
  isUser?: boolean;
  children: ReactNode;
};

export default function ChatBubble({ isUser, children }: Props) {
  const variants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };
  const base = isUser ? 'bg-primary text-primary-foreground ml-auto' : 'bg-muted';
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={variants}
      className={`mb-2 max-w-lg rounded-2xl p-3 shadow ${base}`}
    >
      {children}
    </motion.div>
  );
}
