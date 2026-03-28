import { useState } from 'react';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';

export default function Orders() {
  const [orders] = useState([
    { id: 'ORD-892', customer: '+91 98765 43210', items: 2, total: 410, status: 'preparing', time: '10 mins ago', ai_managed: true },
    { id: 'ORD-891', customer: '+91 87654 32109', items: 1, total: 280, status: 'ready', time: '25 mins ago', ai_managed: false },
    { id: 'ORD-890', customer: '+91 76543 21098', items: 4, total: 1150, status: 'delivered', time: '1 hour ago', ai_managed: true }
  ]);

  const statusColor = {
    pending: 'warning',
    preparing: 'info',
    ready: 'success',
    delivered: 'neutral',
    cancelled: 'error'
  };

  const statusGlow = {
    pending: 'border-l-amber-500',
    preparing: 'border-l-blue-500',
    ready: 'border-l-emerald-500',
    delivered: 'border-l-gray-500',
    cancelled: 'border-l-red-500'
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Live Orders</h1>
        <p className="mt-1 text-sm text-gray-500">Track incoming customer orders in real-time.</p>
      </div>

      <div className="grid gap-4">
        {orders.map((order) => (
          <div key={order.id} className={`bg-white/[0.03] border border-white/[0.06] rounded-xl border-l-[3px] ${statusGlow[order.status]} hover:bg-white/[0.04] transition-all duration-200 cursor-pointer`}>
            <div className="p-5 flex flex-col sm:flex-row justify-between sm:items-center">
              <div>
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-lg text-gray-100 font-mono">{order.id}</span>
                  <Badge variant={statusColor[order.status]}>{order.status.toUpperCase()}</Badge>
                  {order.ai_managed && (
                    <Badge variant="primary">🤖 AI Curated</Badge>
                  )}
                </div>
                <div className="mt-2 text-sm text-gray-400">
                  {order.customer} • {order.items} item(s) • <span className="text-emerald-400 font-mono font-semibold">₹{order.total}</span>
                </div>
              </div>
              <div className="mt-4 sm:mt-0 flex flex-col sm:items-end">
                <span className="text-sm text-gray-500 mb-2">{order.time}</span>
                <select className="text-sm bg-white/[0.04] border border-white/[0.1] rounded-lg text-gray-300 px-3 py-1.5 focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50">
                  <option value="pending">Pending</option>
                  <option value="preparing">Preparing</option>
                  <option value="ready">Ready</option>
                  <option value="delivered">Delivered</option>
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
