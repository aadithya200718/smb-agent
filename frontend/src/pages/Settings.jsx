import { useState } from 'react';
import Card from '../components/common/Card';
import Toggle from '../components/common/Toggle';
import Button from '../components/common/Button';
import Tabs from '../components/common/Tabs';
import { Settings2, Volume2, Globe, ShieldCheck } from 'lucide-react';

export default function Settings() {
  const [activeTab, setActiveTab] = useState('lang');
  const [config, setConfig] = useState({
    autoTranslate: true,
    voiceEnabled: true,
    voiceFemale: true,
    proactiveEnabled: true,
    strictValidation: false,
    recommendationsEnabled: true,
  });

  const handleToggle = (key) => {
    setConfig({ ...config, [key]: !config[key] });
  };

  const tabs = [
    { id: 'lang', label: 'Language', icon: Globe },
    { id: 'voice', label: 'Voice & Media', icon: Volume2 },
    { id: 'agent', label: 'Agent Config', icon: Settings2 },
    { id: 'safety', label: 'Safety & Limits', icon: ShieldCheck }
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Configure AI boundaries and UX parameters.</p>
      </div>

      <Card className="!p-0 overflow-hidden">
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} className="px-6 pt-2" />
        
        <div className="p-6 space-y-8">
          {activeTab === 'lang' && (
            <div className="space-y-6 border-b border-white/[0.06] pb-6">
              <h3 className="text-lg font-medium text-gray-100">Bilingual & Localization</h3>
              <Toggle 
                enabled={config.autoTranslate} 
                onChange={() => handleToggle('autoTranslate')}
                label="Enable Auto-Translation"
                description="Automatically detect Hindi/English and respond in the user's preferred language."
              />
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Default Fallback Language</label>
                <select className="block w-full bg-white/[0.04] border border-white/[0.08] rounded-lg text-gray-200 py-2.5 px-3 text-sm focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50">
                  <option>English</option>
                  <option>Hindi</option>
                  <option>Hinglish (Mixed)</option>
                </select>
              </div>
            </div>
          )}

          {activeTab === 'voice' && (
            <div className="space-y-6 border-b border-white/[0.06] pb-6">
              <h3 className="text-lg font-medium text-gray-100">Voice Capabilities</h3>
              <Toggle 
                enabled={config.voiceEnabled} 
                onChange={() => handleToggle('voiceEnabled')}
                label="Process Voice Messages"
                description="Transcribe incoming audio messages using Google Web Speech API."
              />
              <Toggle 
                enabled={config.voiceFemale} 
                onChange={() => handleToggle('voiceFemale')}
                label="Female Standard Voice Identity"
                description="Use Hindi Female Voice-D for generated audio replies."
              />
            </div>
          )}

          {activeTab === 'agent' && (
            <div className="space-y-6 border-b border-white/[0.06] pb-6">
              <h3 className="text-lg font-medium text-gray-100">Autonomy Parameters</h3>
              <Toggle 
                enabled={config.recommendationsEnabled} 
                onChange={() => handleToggle('recommendationsEnabled')}
                label="Smart Upselling"
                description="Allow the agent to recommend FBT (Frequently Bought Together) items."
              />
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Max Retry Budget</label>
                <input type="number" defaultValue={2} min={0} max={5} className="block w-full bg-white/[0.04] border border-white/[0.08] rounded-lg text-gray-200 py-2.5 px-3 text-sm focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50" />
                <p className="mt-1.5 text-xs text-gray-500">How many times the agent can self-correct failures before throwing an error.</p>
              </div>
            </div>
          )}

          {activeTab === 'safety' && (
            <div className="space-y-6 border-b border-white/[0.06] pb-6">
              <h3 className="text-lg font-medium text-gray-100">Safety & Limits</h3>
              <Toggle 
                enabled={config.strictValidation} 
                onChange={() => handleToggle('strictValidation')}
                label="Strict Output Validation"
                description="Enforce stricter checks on agent responses before sending to customers."
              />
              <Toggle 
                enabled={config.proactiveEnabled} 
                onChange={() => handleToggle('proactiveEnabled')}
                label="Proactive Engagement"
                description="Allow the system to send promotional messages to inactive customers."
              />
            </div>
          )}

          <div className="flex justify-end pt-2">
            <Button>Save Configuration</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
