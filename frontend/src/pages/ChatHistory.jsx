import { useState } from 'react';
import Badge from '../components/common/Badge';
import { Play, Pause, Search } from 'lucide-react';

function VoiceMessagePlayer({ language }) {
  const [playing, setPlaying] = useState(false);
  
  return (
    <div className="bg-primary-500/10 p-3 rounded-lg border border-primary-500/20 max-w-sm mt-2">
      <div className="flex items-center space-x-3">
        <button
          onClick={() => setPlaying(!playing)}
          className="w-10 h-10 rounded-full bg-gradient-to-r from-primary-500 to-primary-600 text-white flex items-center justify-center hover:from-primary-400 hover:to-primary-500 transition-all shadow-lg shadow-primary-500/20"
        >
          {playing ? <Pause size={18} /> : <Play size={18} />}
        </button>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-200">Voice Message</span>
            <Badge variant="info">{language === 'hi' ? '🇮🇳 Hindi' : '🇬🇧 English'}</Badge>
          </div>
          <div className="w-full bg-primary-500/20 h-1 rounded-full mt-2 overflow-hidden">
            <div className={`bg-primary-400 h-full ${playing ? 'w-1/2' : 'w-0'} transition-all duration-1000`}></div>
          </div>
        </div>
      </div>
      <div className="mt-2 text-xs text-gray-500 border-t border-primary-500/15 pt-2 font-mono">
        Transcript: "I want to order 2 butter chicken"
      </div>
    </div>
  );
}

function SentimentIndicator({ sentiment, score }) {
  const config = {
    positive: { emoji: '😊', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    neutral: { emoji: '😐', color: 'text-gray-400', bg: 'bg-white/[0.06]' },
    negative: { emoji: '😞', color: 'text-red-400', bg: 'bg-red-500/10' }
  };
  const { emoji, color, bg } = config[sentiment] || config.neutral;
  
  return (
    <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full ${bg} ${color}`}>
      <span className="text-base">{emoji}</span>
      <span className="text-xs font-medium">
        {sentiment} ({(score * 100).toFixed(0)}%)
      </span>
    </div>
  );
}

export default function ChatHistory() {
  const [chats] = useState([
    {
      id: 1, phone: '+91 98765 43210', messages: [
        { role: 'user', type: 'voice', language: 'hi', time: '10:45 AM' },
        { role: 'assistant', text: 'जी बिल्कुल, मैंने 2 बटर चिकन आपके ऑर्डर में जोड़ दिए हैं।', time: '10:45 AM', sentiment: 'positive', score: 0.95 }
      ]
    },
    {
      id: 2, phone: '+91 87654 32109', messages: [
        { role: 'user', type: 'image', text: 'Can you deliver this?', time: 'Yesterday' },
        { role: 'assistant', text: 'Based on your image I found: Garlic Naan (₹60). Would you like to order?', time: 'Yesterday', sentiment: 'neutral', score: 0.80 }
      ]
    }
  ]);

  return (
    <div className="space-y-6 flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex justify-between items-end flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Chat History</h1>
          <p className="mt-1 text-sm text-gray-500">Live conversation transcripts with sentiment tracking.</p>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden bg-surface-300 rounded-xl border border-white/[0.06]">
        {/* Chat List Sidebar */}
        <div className="w-1/3 border-r border-white/[0.06] flex flex-col">
          <div className="p-4 border-b border-white/[0.06]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-gray-500" size={16} />
              <input type="text" placeholder="Search phone..." className="w-full pl-10 pr-4 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-gray-200 placeholder:text-gray-500 focus:ring-1 focus:ring-primary-500/30 focus:border-primary-500/50" />
            </div>
          </div>
          <div className="overflow-y-auto flex-1 p-2 space-y-1">
            {chats.map(chat => (
              <div key={chat.id} className={`p-3 rounded-lg cursor-pointer transition-all ${chat.id === 1 ? 'bg-primary-500/10 border border-primary-500/20' : 'hover:bg-white/[0.03] border border-transparent'}`}>
                <div className="font-medium text-sm text-gray-200">{chat.phone}</div>
                <div className="text-xs text-gray-500 mt-1 truncate">Last active: {chat.messages[1].time}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Window */}
        <div className="w-2/3 flex flex-col bg-[#0a0e14]">
          <div className="p-4 border-b border-white/[0.06] bg-surface-300 flex justify-between items-center">
            <h3 className="font-semibold text-gray-200">{chats[0].phone}</h3>
            <div className="flex space-x-2">
               <SentimentIndicator sentiment="positive" score={0.92} />
               <Badge>Lang: hi/en</Badge>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
             {chats[0].messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <span className="text-xs text-gray-600 mb-1 mx-1">{msg.time}</span>
                  {msg.role === 'assistant' ? (
                     <div className="bg-surface-50 border border-white/[0.06] rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%]">
                        <p className="text-gray-200 text-sm">{msg.text}</p>
                     </div>
                  ) : (
                     <div className="bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] shadow-lg shadow-primary-500/10">
                        {msg.type === 'voice' ? (
                          <VoiceMessagePlayer language={msg.language} />
                        ) : (
                          <p className="text-sm">{msg.text || 'Image attached'}</p>
                        )}
                     </div>
                  )}
                </div>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
}
