'use client';
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
  const base = isUser
    ? 'bg-blue-500 text-white ml-auto dark:bg-blue-600'
    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100';
  const MotionDiv = motion<HTMLDivElement>('div');
  return (
    <MotionDiv
      initial="hidden"
      animate="visible"
      variants={variants}
      className={`mb-2 max-w-lg rounded-2xl p-3 shadow ${base}`}
    >
      {children}
    </MotionDiv>
  );
}
