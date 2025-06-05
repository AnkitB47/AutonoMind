'use client';
import { ThemeToggle } from '../Shared/ThemeToggle';

export default function TopNav() {
  return (
    <nav className="flex items-center justify-between border-b p-4 shadow">
      <div className="font-bold">AutonoMind</div>
      <div className="flex items-center gap-3">
        <ThemeToggle />
      </div>
    </nav>
  );
}
