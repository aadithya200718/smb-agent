export default function Card({ title, children, actions, className = '', glowOnHover = false }) {
  return (
    <div className={`
      bg-white/[0.03] backdrop-blur-sm border border-white/[0.06] rounded-xl overflow-hidden
      transition-all duration-300
      ${glowOnHover ? 'hover:border-primary/30 hover:shadow-glow-sm' : ''}
      ${className}
    `}>
      {(title || actions) && (
        <div className="px-6 py-4 border-b border-white/[0.06] flex items-center justify-between">
          {title && <h3 className="text-lg font-semibold text-gray-100">{title}</h3>}
          {actions && <div className="flex space-x-2">{actions}</div>}
        </div>
      )}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
}
