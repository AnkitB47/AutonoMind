import '../styles/globals.css';
import type { ReactNode } from 'react';
import { ChatProvider } from "../context/ChatProvider";
import { ThemeProvider } from '../context/ThemeProvider';
import Script from 'next/script';

export default function RootLayout({ children }: { children: ReactNode }) {
   return (
    <html lang="en">
      <head>
        <Script src="/env.js" strategy="beforeInteractive" />
      </head>
      <body className="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
        <ThemeProvider>
          <ChatProvider>{children}</ChatProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
