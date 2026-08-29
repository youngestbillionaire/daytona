import React, { useState } from 'react';
import { Globe, ExternalLink, RefreshCw, Smartphone, Monitor } from 'lucide-react';

interface LiveMVPPreviewProps {
  previewUrl?: string;
  productName?: string;
}

export default function LiveMVPPreview({ previewUrl, productName }: LiveMVPPreviewProps) {
  const [deviceMode, setDeviceMode] = useState<'desktop' | 'mobile'>('desktop');
  const [iframeKey, setIframeKey] = useState(0);

  if (!previewUrl) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-8 shadow-2xl flex flex-col items-center justify-center min-h-[400px] text-center">
        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4 animate-pulse">
          <Globe className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Live Daytona MVP Sandbox</h3>
        <p className="text-slate-400 text-xs max-w-md font-mono">
          The running prototype will be deployed and embedded here in real time once Stage 12 (MVP_DEPLOY_PREVIEW) succeeds.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-5 shadow-2xl flex flex-col h-[520px]">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-xs font-bold text-white">{productName || 'Generated MVP'}</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-800">
            Daytona Live Preview
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setDeviceMode('desktop')}
            className={`p-1.5 rounded-lg text-xs ${deviceMode === 'desktop' ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}
          >
            <Monitor className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setDeviceMode('mobile')}
            className={`p-1.5 rounded-lg text-xs ${deviceMode === 'mobile' ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}
          >
            <Smartphone className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIframeKey(k => k + 1)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs"
            title="Reload Frame"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
          >
            <span>Open Tab</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      <div className="flex-1 w-full flex items-center justify-center bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 relative">
        <div className={`h-full transition-all duration-300 ${deviceMode === 'mobile' ? 'w-[375px] border-x border-slate-700' : 'w-full'}`}>
          <iframe
            key={iframeKey}
            src={previewUrl}
            title="Live Daytona Preview"
            className="w-full h-full border-none rounded-xl"
          />
        </div>
      </div>
    </div>
  );
}
