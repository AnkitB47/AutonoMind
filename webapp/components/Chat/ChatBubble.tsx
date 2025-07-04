'use client';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type Props = {
  isUser?: boolean;
  source?: string | null;
  children: ReactNode;
};

export default function ChatBubble({ isUser, source, children }: Props) {
  const variants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };
  const base = isUser
    ? 'bg-blue-500 text-white ml-auto dark:bg-blue-600'
    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100';
  const MotionDiv = motion<HTMLDivElement>('div');
  return (
    <MotionDiv
      initial="hidden"
      animate="visible"
      variants={variants}
      className={`mb-2 max-w-lg flex items-start gap-2 rounded-2xl p-3 shadow ${base}`}
    >
      {!isUser && <div className="h-6 w-6 rounded-full bg-primary" />}
      <div className="flex-1">
        {children}
        {source && (
          <div className="mt-1 text-xs text-muted-foreground">source: {source.toUpperCase()}</div>
        )}
      </div>
    </MotionDiv>
  );
}
