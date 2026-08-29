import React, { useState } from 'react';
import { Presentation, Download, ExternalLink, Maximize2 } from 'lucide-react';

interface PitchDeckViewerProps {
  deckUrl?: string;
  productName?: string;
  narrationScript?: string;
}

export default function PitchDeckViewer({ deckUrl, productName, narrationScript }: PitchDeckViewerProps) {
  const [activeTab, setActiveTab] = useState<'deck' | 'narration'>('deck');

  if (!deckUrl) {
    return (
      <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-8 shadow-2xl flex flex-col items-center justify-center min-h-[380px] text-center">
        <div className="w-16 h-16 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mb-4 animate-pulse">
          <Presentation className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Venture Pitch Deck & Narration</h3>
        <p className="text-slate-400 text-xs max-w-md font-mono">
          The synthesized 7-slide deck and 45-second spoken pitch script will be rendered here upon reaching Stage 15 (DECK_GENERATION).
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-5 shadow-2xl flex flex-col h-[520px]">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Presentation className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-bold text-white">{productName} Investor Deck</span>
          </div>
          <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-[11px] font-mono">
            <button
              onClick={() => setActiveTab('deck')}
              className={`px-3 py-1 rounded-lg transition-all ${activeTab === 'deck' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
            >
              7-Slide Deck
            </button>
            <button
              onClick={() => setActiveTab('narration')}
              className={`px-3 py-1 rounded-lg transition-all ${activeTab === 'narration' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
            >
              Audio Pitch Script
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={deckUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs transition-colors"
          >
            <span>Full View</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      <div className="flex-1 w-full bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 relative">
        {activeTab === 'deck' ? (
          <iframe
            src={deckUrl}
            title="Pitch Deck Viewer"
            className="w-full h-full border-none rounded-xl"
          />
        ) : (
          <div className="p-6 overflow-y-auto h-full flex flex-col justify-center max-w-2xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-mono mb-4 mx-auto">
              🎙️ 45-Second Spoken Pitch Cadence
            </div>
            <p className="text-base text-slate-200 leading-relaxed italic bg-slate-900/80 p-6 rounded-2xl border border-slate-800">
              "{narrationScript || 'Loading narration script...'}"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
