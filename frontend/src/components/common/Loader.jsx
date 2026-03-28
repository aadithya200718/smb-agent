import { Loader2 } from 'lucide-react';

export default function Loader({ fullScreen = false, size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const icon = <Loader2 className={`animate-spin text-primary-400 ${sizeClasses[size]} ${className}`} />;

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-[#0a0e14]/90 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          {icon}
          <span className="text-sm text-gray-400 animate-pulse">Loading…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-8">
      {icon}
    </div>
  );
}
