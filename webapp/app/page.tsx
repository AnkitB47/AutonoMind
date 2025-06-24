import ChatWindow from '../components/Chat/ChatWindow';
import Sidebar from '../components/Layout/Sidebar';
import TopNav from '../components/Layout/TopNav';
import RightPanel from '../components/Layout/RightPanel';

export const dynamic = 'force-dynamic';

export default function Home() {
  return (
    <div className="flex h-screen flex-col">
      <TopNav />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatWindow />
        <RightPanel />
      </div>
    </div>
  );
}
