import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      {/* Main content with bottom padding on mobile for tab bar */}
      <main className="pb-20 md:pb-0">
        <Outlet />
      </main>
    </div>
  );
}
