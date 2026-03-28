import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { 
  Home, UtensilsCrossed, ShoppingBag, MessageSquare, 
  Activity, Send, BarChart3, Settings, LogOut, X, Zap 
} from 'lucide-react';
import Badge from '../common/Badge';

const navigation = [
  { name: 'Dashboard', path: '/dashboard', icon: Home },
  { name: 'Menu', path: '/menu', icon: UtensilsCrossed },
  { name: 'Orders', path: '/orders', icon: ShoppingBag },
  { name: 'Chats', path: '/chats', icon: MessageSquare },
  { name: 'Autonomy Monitor', path: '/autonomy-monitor', icon: Activity, badge: 'Live', badgeColor: 'success' },
  { name: 'Engagement', path: '/engagement', icon: Send },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'Settings', path: '/settings', icon: Settings }
];

export default function Sidebar({ mobileMenuOpen, setMobileMenuOpen }) {
  const location = useLocation();
  const { logout } = useAuth();
  
  const NavLinks = () => (
    <div className="space-y-1 px-3 py-4">
      {navigation.map((item) => {
        const isActive = location.pathname.startsWith(item.path);
        return (
          <Link
            key={item.name}
            to={item.path}
            onClick={() => setMobileMenuOpen(false)}
            className={`
              group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200
              ${isActive 
                ? 'bg-primary-500/10 text-primary-400 border border-primary-500/20' 
                : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-200 border border-transparent'
              }
            `}
          >
            <div className="flex items-center">
              <item.icon className={`mr-3 h-[18px] w-[18px] flex-shrink-0 ${isActive ? 'text-primary-400' : 'text-gray-500 group-hover:text-gray-400'}`} />
              {item.name}
            </div>
            {item.badge && (
              <Badge variant={item.badgeColor || 'primary'}>{item.badge}</Badge>
            )}
          </Link>
        );
      })}
    </div>
  );

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      <div className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity lg:hidden ${mobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} onClick={() => setMobileMenuOpen(false)} />

      {/* Sidebar Component */}
      <div className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-surface-300 border-r border-white/[0.06] transition-transform lg:static lg:translate-x-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        
        {/* Mobile close button */}
        <div className="absolute top-0 right-0 -mr-12 pt-4 lg:hidden">
          <button
            type="button"
            className={`ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white ${mobileMenuOpen ? 'block' : 'hidden'}`}
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="sr-only">Close sidebar</span>
            <X className="h-6 w-6 text-white" aria-hidden="true" />
          </button>
        </div>

        {/* Logo area */}
        <div className="flex h-16 flex-shrink-0 items-center px-6 border-b border-white/[0.06]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <span className="font-bold text-gray-100 text-sm">AI Assistant</span>
              <span className="block text-[10px] text-gray-500 font-medium -mt-0.5">QSR Platform</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex flex-1 flex-col overflow-y-auto">
          <nav className="flex-1 py-2">
            <NavLinks />
          </nav>
        </div>
        
        {/* Demo link */}
        <div className="px-3 pb-2">
          <Link
            to="/demo"
            className="flex items-center rounded-lg px-3 py-2.5 text-sm font-medium text-accent-400 bg-accent-500/10 border border-accent-500/20 hover:bg-accent-500/20 transition-all"
          >
            <Zap className="mr-3 h-[18px] w-[18px]" />
            Live Demo
          </Link>
        </div>

        {/* Logout bottom pinned */}
        <div className="border-t border-white/[0.06] p-4">
          <button 
            onClick={logout}
            className="flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="mr-3 h-[18px] w-[18px]" />
            Sign Out
          </button>
        </div>
      </div>
    </>
  );
}
