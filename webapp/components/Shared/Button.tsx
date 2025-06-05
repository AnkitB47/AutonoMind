'use client';
import { ComponentProps } from 'react';

export function Button({ className = '', ...props }: ComponentProps<'button'>) {
  return (
    <button
      className={`rounded-2xl bg-primary px-3 py-2 text-primary-foreground shadow hover:opacity-90 ${className}`}
      {...props}
    />
  );
}
