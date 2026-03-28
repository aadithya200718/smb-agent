export default function Tabs({ tabs, activeTab, onChange, className = '' }) {
  return (
    <div className={`border-b border-white/[0.06] ${className}`}>
      <nav className="-mb-px flex space-x-6" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                whitespace-nowrap py-3.5 px-1 border-b-2 font-medium text-sm transition-all duration-200
                ${isActive
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-white/[0.15]'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="flex items-center space-x-2">
                {tab.icon && <tab.icon size={16} />}
                <span>{tab.label}</span>
              </div>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
