'use client';
import { ThemeToggle } from '../Shared/ThemeToggle';
import { useContext } from 'react';
import { ChatContext } from '../../context/ChatProvider';

export default function TopNav() {
  const { language, setLanguage, apiChoice, setApiChoice } = useContext(ChatContext);
  return (
    <nav className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow text-gray-900 dark:text-gray-100">
      <div className="font-bold">AutonoMind</div>
      <div className="flex items-center gap-3">
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="en">EN</option>
          <option value="de">DE</option>
          <option value="fr">FR</option>
          <option value="hi">HI</option>
        </select>
        <select
          value={apiChoice}
          onChange={(e) => setApiChoice(e.target.value as 'fastapi' | 'streamlit')}
          className="rounded border px-2 py-1 text-sm"
        >
          <option value="streamlit">Streamlit</option>
          <option value="fastapi">FastAPI</option>
        </select>
        <ThemeToggle />
      </div>
    </nav>
  );
}
