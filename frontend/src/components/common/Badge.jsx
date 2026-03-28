export default function Badge({ children, variant = 'neutral', className = '' }) {
  const variantClasses = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    neutral: 'bg-white/[0.06] text-gray-400 border-white/[0.1]',
    primary: 'bg-primary-500/10 text-primary-400 border-primary-500/20',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variantClasses[variant] || variantClasses.neutral} ${className}`}>
      {children}
    </span>
  );
}
