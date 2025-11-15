import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import BottomNav from './BottomNav';

export default function Layout() {
  return (
    <div className="bg-background">
      {/* Desktop Navbar - hidden on mobile */}
      <Navbar />
      
      {/* Main content with padding for fixed navbars */}
      <main className="pb-20 md:pb-0">
        <Outlet />
      </main>
      
      {/* Mobile Bottom Navigation - hidden on desktop */}
      <BottomNav />
    </div>
  );
}
