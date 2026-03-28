import { useState } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import Input from '../components/common/Input';
import Modal from '../components/common/Modal';
import { Send, Calendar, Users, TrendingUp } from 'lucide-react';

export default function EngagementCampaigns() {
  const [campaigns] = useState([
    { id: 1, name: 'Weekend Special Offer', type: 'promo', audience: 'All Users', sent: 1450, responses: 240, status: 'completed', date: 'Oct 12, 2026' },
    { id: 2, name: 'Re-engage Inactive (30d)', type: 're_engagement', audience: 'Inactive > 30d', sent: 320, responses: 18, status: 'active', date: 'Oct 14, 2026' },
    { id: 3, name: 'Diwali Menu Announcement', type: 'announcement', audience: 'VIP Customers', sent: 0, responses: 0, status: 'scheduled', date: 'Tomorrow, 10:00 AM' }
  ]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Proactive Engagement</h1>
          <p className="mt-1 text-sm text-gray-500">Manage automated outbound WhatsApp campaigns.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="flex items-center">
          <Send size={16} className="mr-2" /> New Campaign
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {[
          { icon: Send, label: 'Total Sent', value: '1,770', gradient: 'stat-gradient-blue', iconBg: 'bg-blue-500/15 text-blue-400' },
          { icon: TrendingUp, label: 'Avg Response Rate', value: '14.5%', gradient: 'stat-gradient-green', iconBg: 'bg-emerald-500/15 text-emerald-400' },
          { icon: Users, label: 'Reach', value: '4,200', gradient: 'stat-gradient-purple', iconBg: 'bg-purple-500/15 text-purple-400' },
        ].map((stat) => (
          <div key={stat.label} className={`flex items-center p-5 rounded-xl ${stat.gradient}`}>
            <div className={`p-3 rounded-xl mr-4 ${stat.iconBg}`}><stat.icon size={22} /></div>
            <div><p className="text-sm text-gray-400">{stat.label}</p><p className="text-xl font-bold text-gray-100">{stat.value}</p></div>
          </div>
        ))}
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/[0.06]">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campaign</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Audience</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Performance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {campaigns.map(camp => (
                <tr key={camp.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-200">{camp.name}</div>
                    <div className="text-xs text-gray-500 flex items-center mt-1">
                      <Calendar size={11} className="mr-1" /> {camp.date}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{camp.audience}</td>
                  <td className="px-6 py-4">
                    <Badge variant={camp.status === 'completed' ? 'neutral' : camp.status === 'active' ? 'success' : 'warning'}>
                      {camp.status.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-300">{camp.sent} sent</div>
                    {camp.sent > 0 && <div className="text-xs text-emerald-400 mt-1">{((camp.responses / camp.sent) * 100).toFixed(1)}% conversion</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Create Engagement Campaign">
        <div className="space-y-4">
          <Input label="Campaign Name" placeholder="e.g. Diwali Weekend Special" />
          <div>
             <label className="block text-sm font-medium text-gray-300 mb-1.5">Target Audience</label>
             <select className="w-full rounded-lg bg-white/[0.04] border border-white/[0.08] text-gray-200 py-2.5 px-3 text-sm focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50">
               <option>All Past Customers</option>
               <option>Inactive (&gt;30 days)</option>
               <option>High Value (VIP)</option>
             </select>
          </div>
          <div>
             <label className="block text-sm font-medium text-gray-300 mb-1.5">Message Template (AI will personalize)</label>
             <textarea rows="4" className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg text-gray-200 text-sm p-3 placeholder:text-gray-500 focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50" placeholder="Hi {name}, we've missed you! Here's a quick update..."></textarea>
          </div>
          <div className="pt-4 flex justify-end space-x-3">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={() => setIsModalOpen(false)}>Schedule Campaign</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
