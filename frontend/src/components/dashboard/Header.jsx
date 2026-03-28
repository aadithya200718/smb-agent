import { Menu, Bell } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export default function Header({ setMobileMenuOpen }) {
  const { user } = useAuth();
  
  return (
    <header className="sticky top-0 z-30 flex h-16 flex-shrink-0 bg-surface-300/80 backdrop-blur-md border-b border-white/[0.06]">
      <button
        type="button"
        className="border-r border-white/[0.06] px-4 text-gray-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 lg:hidden"
        onClick={() => setMobileMenuOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Menu className="h-5 w-5" aria-hidden="true" />
      </button>
      
      <div className="flex flex-1 justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex flex-1 items-center">
          <h2 className="text-lg font-semibold text-gray-200 hidden sm:block">
            {user?.business_name || 'Business Dashboard'}
          </h2>
        </div>
        
        <div className="ml-4 flex items-center md:ml-6 space-x-4">
          {/* Notification bell */}
          <button className="relative p-2 rounded-lg text-gray-400 hover:bg-white/[0.04] hover:text-gray-200 transition-colors">
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary-500 rounded-full"></span>
          </button>

          {/* User avatar */}
          <div className="flex items-center space-x-3">
             <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-primary-500/20">
               {user?.email?.charAt(0).toUpperCase() || 'U'}
             </div>
             <div className="hidden md:block">
                <p className="text-sm font-medium text-gray-200">{user?.email}</p>
                <p className="text-xs text-gray-500">Admin</p>
             </div>
          </div>
        </div>
      </div>
    </header>
  );
}
