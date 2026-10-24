import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import DashboardNavbar from '../components/layout/DashboardNavbar';

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // If on /analysis/:id (review workspace), let it use full width, otherwise give standard padded container
  const isReviewWorkspace =
    location.pathname.startsWith('/analysis/') && location.pathname !== '/analysis/new';

  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--text-main)] flex">
      {/* Keyboard-accessible skip link */}
      <a href="#main-content" className="skip-to-main-link">
        Skip to main content
      </a>

      {/* Sidebar Navigation Rail (220px) */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 md:pl-[220px]">
        <DashboardNavbar onOpenSidebar={() => setSidebarOpen(true)} />

        <main
          id="main-content"
          tabIndex={-1}
          className={`flex-1 ${
            isReviewWorkspace
              ? 'p-3 sm:p-4 lg:p-6 w-full'
              : 'p-4 sm:p-6 lg:p-8 max-w-[1200px] w-full mx-auto'
          }`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
