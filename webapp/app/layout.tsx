import '../styles/globals.css';
import type { ReactNode } from 'react';
import { ChatProvider } from "../context/ChatProvider";
import { ThemeProvider } from '../context/ThemeProvider';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">␊
      <body className="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
        <ThemeProvider>
        <ChatProvider>
          {children}
        </ChatProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
