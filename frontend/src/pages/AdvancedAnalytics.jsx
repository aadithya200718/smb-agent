import { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Loader from '../components/common/Loader';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';

const mockDailyOrders = [
  { date: 'Mon', orders: 12, ai_handled: 10 },
  { date: 'Tue', orders: 19, ai_handled: 15 },
  { date: 'Wed', orders: 15, ai_handled: 13 },
  { date: 'Thu', orders: 22, ai_handled: 18 },
  { date: 'Fri', orders: 29, ai_handled: 25 },
  { date: 'Sat', orders: 35, ai_handled: 30 },
  { date: 'Sun', orders: 28, ai_handled: 22 },
];

const mockLanguageSplit = [
  { name: 'Hindi', value: 65 },
  { name: 'English', value: 30 },
  { name: 'Hinglish', value: 5 }
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-300 border border-white/[0.1] rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-medium" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
};

export default function AdvancedAnalytics() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => setLoading(false), 500);
  }, []);

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Advanced Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">Deep dive into ROI and feature usage metrics.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <Card title="Order Volume (Last 7 Days)">
          <div className="h-72 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockDailyOrders}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6b7280', fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="orders" name="Total Orders" stroke="#6366f1" strokeWidth={3} dot={{ fill: '#6366f1', strokeWidth: 0, r: 4 }} />
                <Line type="monotone" dataKey="ai_handled" name="Handled by AI" stroke="#10b981" strokeWidth={3} dot={{ fill: '#10b981', strokeWidth: 0, r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Language Distribution">
          <div className="h-72 mt-4">
             <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockLanguageSplit} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" width={80} tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" name="Percentage" fill="#8b5cf6" radius={[0, 6, 6, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Feature Impact / ROI">
          <div className="space-y-6">
            {[
              { name: 'Recommendations (Smart Upsell)', value: '+₹45,200', percent: 85, color: 'from-emerald-500 to-emerald-400', textColor: 'text-emerald-400' },
              { name: 'Proactive Engagement', value: '+₹18,500', percent: 45, color: 'from-blue-500 to-blue-400', textColor: 'text-blue-400' },
              { name: 'Voice Ordering Conv. Rate', value: '62%', percent: 62, color: 'from-purple-500 to-purple-400', textColor: 'text-purple-400' },
            ].map((item) => (
              <div key={item.name}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-300">{item.name}</span>
                  <span className={`text-sm font-bold ${item.textColor}`}>{item.value}</span>
                </div>
                <div className="w-full bg-white/[0.06] rounded-full h-2">
                  <div className={`bg-gradient-to-r ${item.color} h-2 rounded-full transition-all duration-1000`} style={{ width: `${item.percent}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Sentiment Trends">
          <div className="flex items-center justify-center space-x-10 h-full min-h-[200px]">
            {[
              { emoji: '😊', value: '78%', label: 'Positive', opacity: '' },
              { emoji: '😐', value: '18%', label: 'Neutral', opacity: 'opacity-60' },
              { emoji: '😞', value: '4%', label: 'Negative', opacity: 'opacity-40' },
            ].map((item) => (
              <div key={item.label} className={`text-center ${item.opacity}`}>
                <div className="text-4xl mb-3">{item.emoji}</div>
                <div className="text-2xl font-bold text-gray-100">{item.value}</div>
                <div className="text-sm text-gray-500 mt-1">{item.label}</div>
              </div>
            ))}
          </div>
        </Card>

      </div>
    </div>
  );
}
