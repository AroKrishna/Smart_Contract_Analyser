import { Outlet } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

const PublicLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--text-main)] flex flex-col">
      <a href="#landing-content" className="skip-to-main-link">
        Skip to main content
      </a>
      <Navbar />
      <main id="landing-content" tabIndex={-1} className="flex-1">
        {children || <Outlet />}
      </main>
      <Footer />
    </div>
  );
};

export default PublicLayout;
