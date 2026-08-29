import React from 'react';
import { Sparkles, Terminal, Activity, Layers } from 'lucide-react';

interface NavbarProps {
  currentTab: 'launch' | 'live' | 'history';
  setCurrentTab: (tab: 'launch' | 'live' | 'history') => void;
  activeRunId?: string;
}

export default function Navbar({ currentTab, setCurrentTab, activeRunId }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 bg-[#030712]/80 backdrop-blur-xl border-b border-slate-800/80 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('launch')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-sky-400 to-blue-600 flex items-center justify-center font-black text-slate-950 text-xl shadow-lg shadow-cyan-500/20">
            F0
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-white tracking-tight">FOUNDER-0</span>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">Autonomous Multi-Agent Venture Engine</p>
          </div>
        </div>
      </div>

      <nav className="flex items-center space-x-1 bg-slate-900/80 p-1.5 rounded-2xl border border-slate-800">
        <button
          onClick={() => setCurrentTab('launch')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            currentTab === 'launch'
              ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>New Venture</span>
        </button>

        {activeRunId && (
          <button
            onClick={() => setCurrentTab('live')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              currentTab === 'live'
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-4 h-4 animate-pulse text-emerald-400" />
            <span>Active Pipeline</span>
          </button>
        )}

        <button
          onClick={() => setCurrentTab('history')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            currentTab === 'history'
              ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Run History</span>
        </button>
      </nav>
    </header>
  );
}
