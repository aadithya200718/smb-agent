import { useEffect, useState } from 'react';
import { agentService } from '../services/agentService';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import Loader from '../components/common/Loader';

function AgentStatus({ status, metrics }) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">Agent Status</h3>
          <p className="text-sm text-gray-500">Autonomous loop health</p>
        </div>
        <Badge variant={status === 'healthy' ? 'success' : 'error'}>
          {status}
        </Badge>
      </div>
      
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-emerald-500/[0.07] border border-emerald-500/15 p-4 rounded-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">Validation Pass Rate</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{metrics.validationPassRate}%</div>
        </div>
        <div className="bg-primary-500/[0.07] border border-primary-500/15 p-4 rounded-xl">
          <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">Avg Retry Count</div>
          <div className="text-2xl font-bold text-primary-400 mt-1">{metrics.avgRetryCount}</div>
        </div>
      </div>
    </Card>
  );
}

function TraceLogViewer({ traceLog }) {
  if (!traceLog || traceLog.length === 0) return <div className="text-gray-500 text-sm">No recent traces found.</div>;

  const nodeColors = {
    input: 'bg-blue-500', think: 'bg-purple-500', plan: 'bg-amber-500',
    act: 'bg-emerald-500', review: 'bg-pink-500', update: 'bg-orange-500', respond: 'bg-cyan-500'
  };
  
  return (
    <div className="space-y-3">
      {traceLog.map((entry, index) => (
        <div key={index} className="flex items-start space-x-3 animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
          <div className={`w-2.5 h-2.5 rounded-full mt-2 flex-shrink-0 ${nodeColors[entry.node_name] || 'bg-gray-500'}`} />
          
          <div className="flex-1 bg-white/[0.02] border border-white/[0.05] p-3 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono font-medium text-gray-300 uppercase text-xs tracking-wider">
                {entry.node_name}
              </span>
              <span className="text-xs text-gray-600">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
            
            {entry.decision && <p className="text-sm text-gray-400 font-medium mb-2">{entry.decision}</p>}
            
            {entry.output_summary && Object.keys(entry.output_summary).length > 0 && (
              <pre className="text-xs bg-black/20 p-2 rounded text-gray-500 overflow-x-auto font-mono">
                {JSON.stringify(entry.output_summary, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AutonomyMonitor() {
  const [loading, setLoading] = useState(true);
  
  const [data] = useState({
    status: 'healthy',
    metrics: { validationPassRate: 92.5, avgRetryCount: 0.15 },
    recentTrace: [
      { node_name: 'input', timestamp: new Date().toISOString(), decision: 'Message received', output_summary: { action: 'initialized state' } },
      { node_name: 'think', timestamp: new Date().toISOString(), decision: 'Intent: place_order, Language: hi', output_summary: { intent: 'place_order', language: 'hi' } },
      { node_name: 'plan', timestamp: new Date().toISOString(), decision: 'Tools: [get_menu, create_order]', output_summary: { tools: ['get_menu', 'create_order'] } },
      { node_name: 'act', timestamp: new Date().toISOString(), decision: 'Executed 2 tools', output_summary: { executed: 2, errors: [] } },
      { node_name: 'review', timestamp: new Date().toISOString(), decision: 'PASS', output_summary: { passed: true, confidence_score: 1.0 } },
      { node_name: 'respond', timestamp: new Date().toISOString(), decision: 'SUCCESS_RESPONSE', output_summary: { response_length: 120, language: 'hi' } },
    ]
  });

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (loading) return <Loader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Autonomy Monitor</h1>
        <p className="mt-1 text-sm text-gray-500">Live observability of the AI agent reasoning pipeline.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <AgentStatus status={data.status} metrics={data.metrics} />
          
          <Card title="System Configuration">
            <div className="space-y-3 text-sm">
              {[
                { label: 'Max Retry Budget', value: '2' },
                { label: 'Validation Threshold', value: '0.80' },
                { label: 'Active LLM', value: 'llama-3.3-70b' },
                { label: 'Embedding Model', value: 'all-MiniLM-L6' },
              ].map((item) => (
                <div key={item.label} className="flex justify-between border-b border-white/[0.04] pb-2.5">
                  <span className="text-gray-500">{item.label}</span>
                  <span className="font-medium text-gray-300 font-mono">{item.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
        
        <div className="lg:col-span-2">
          <Card title="Live Trace Log (Latest Execution)">
            <TraceLogViewer traceLog={data.recentTrace} />
          </Card>
        </div>
      </div>
    </div>
  );
}
