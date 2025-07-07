'use client';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type Props = {
  isUser?: boolean;
  source?: string | null;
  children: ReactNode;
  error?: boolean;
};

export default function ChatBubble({ isUser, source, children, error }: Props) {
  const variants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };
  const base = error
    ? 'bg-red-100 border border-red-400 text-red-800 dark:bg-red-900 dark:text-red-200'
    : isUser
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
      {!isUser && !error && <div className="h-6 w-6 rounded-full bg-primary" />}
      {error && (
        <div className="h-6 w-6 flex items-center justify-center rounded-full bg-red-400">
          <span role="img" aria-label="error" className="text-white">⚠️</span>
        </div>
      )}
      <div className="flex-1">
        {children}
        {source && !error && (
          <div className="mt-1 text-xs text-muted-foreground">source: {source.toUpperCase()}</div>
        )}
      </div>
    </MotionDiv>
  );
}
