import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, PhoneCall, TrendingUp, ShoppingBag, ArrowRight, Zap, Activity } from 'lucide-react';
import Card from '../components/common/Card';
import Loader from '../components/common/Loader';

function StatsCard({ title, value, highlight, icon: Icon, trend, gradient }) {
  return (
    <div className={`rounded-xl p-5 ${gradient} transition-all duration-300 hover:scale-[1.02]`}>
      <div className="flex items-center justify-between pb-2">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <Icon className="h-5 w-5 text-gray-500" />
      </div>
      <div className="text-2xl font-bold text-gray-100 mt-1">{value}</div>
      {highlight && <p className="text-xs mt-2 text-gray-400 font-medium">{highlight}</p>}
      {trend && (
        <p className={`text-xs mt-2 font-semibold ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last month
        </p>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => setLoading(false), 300);
  }, []);

  if (loading) return <Loader />;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Dashboard Overview</h1>
        <p className="mt-1 text-sm text-gray-500">Real-time metrics across all AI assistant operations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Total Messages" 
          value="1,245" 
          highlight="60% Hindi / 40% English" 
          icon={MessageSquare} 
          trend={12}
          gradient="stat-gradient-blue"
        />
        <StatsCard 
          title="Voice Usage" 
          value="450" 
          highlight="35% of all traffic" 
          icon={PhoneCall} 
          trend={24}
          gradient="stat-gradient-purple"
        />
        <StatsCard 
          title="Total Orders" 
          value="156" 
          highlight="via AI Assistant" 
          icon={ShoppingBag} 
          trend={8}
          gradient="stat-gradient-green"
        />
        <StatsCard 
          title="Rec. Acceptance" 
          value="45%" 
          highlight="+₹15,000 Revenue Impact" 
          icon={TrendingUp} 
          trend={5}
          gradient="stat-gradient-amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Agent Health Status">
          <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
            <div className="w-16 h-16 bg-emerald-500/15 text-emerald-400 rounded-2xl flex items-center justify-center border border-emerald-500/20">
              <Activity size={32} />
            </div>
            <div>
              <h4 className="text-xl font-bold text-gray-100">Excellent</h4>
              <p className="text-gray-400 mt-2 text-sm">The autonomous agent is handling <span className="text-emerald-400 font-semibold">85%</span> of queries without human escalation.</p>
            </div>
            <div className="w-full bg-white/[0.06] rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded-full transition-all duration-1000" style={{ width: '85%' }}></div>
            </div>
          </div>
        </Card>

        <Card title="Quick Actions">
          <div className="grid grid-cols-2 gap-3">
            {[
              { title: 'Add Menu Item', desc: 'Update your AI catalog', path: '/menu' },
              { title: 'Send Campaign', desc: 'Engage past customers', path: '/engagement' },
              { title: 'View Traces', desc: 'Audit agent decisions', path: '/autonomy-monitor' },
              { title: 'Live Demo', desc: 'Test the AI agent', path: '/demo' },
            ].map((action) => (
              <Link
                key={action.title}
                to={action.path}
                className="group p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl hover:border-primary-500/30 hover:bg-primary-500/[0.04] text-left transition-all duration-300"
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-gray-200 text-sm">{action.title}</h4>
                  <ArrowRight size={14} className="text-gray-600 group-hover:text-primary-400 group-hover:translate-x-0.5 transition-all" />
                </div>
                <p className="text-xs text-gray-500 mt-1">{action.desc}</p>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
