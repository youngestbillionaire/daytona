import React, { useEffect, useRef } from 'react';
import { Terminal, Download, ShieldCheck } from 'lucide-react';
import { StageEvent } from '../types';

interface TerminalLogsProps {
  stages: StageEvent[];
  selectedStage: string;
  liveLogs: string[];
}

export default function TerminalLogs({ stages, selectedStage, liveLogs }: TerminalLogsProps) {
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const currentStageEvent = stages.find(s => s.stage === selectedStage);
  const stageLogs = currentStageEvent?.logs || [];
  const displayLogs = stageLogs.length > 0 ? stageLogs : liveLogs;

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayLogs]);

  return (
    <div className="bg-[#0b0f19] border border-slate-800/80 rounded-3xl p-5 shadow-2xl flex flex-col h-[320px]">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">
            {selectedStage ? `Logs: ${selectedStage}` : 'Realtime Execution Log Stream'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-[10px] font-mono text-slate-400">WebSocket Live</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto font-mono text-xs text-slate-300 space-y-1 pr-2">
        {displayLogs.length === 0 ? (
          <div className="text-slate-600 italic py-8 text-center">
            Awaiting stage execution events...
          </div>
        ) : (
          displayLogs.map((log, idx) => (
            <div key={idx} className="leading-relaxed hover:bg-slate-900/60 px-2 py-0.5 rounded transition-colors">
              <span className="text-slate-500 select-none mr-2">{(idx + 1).toString().padStart(3, '0')}</span>
              <span className={
                log.includes('✅') || log.includes('succeeded') || log.includes('✓') 
                  ? 'text-emerald-400 font-semibold' 
                  : log.includes('❌') || log.includes('failed') || log.includes('Error') 
                  ? 'text-rose-400 font-semibold'
                  : log.includes('⚡') || log.includes('🚀') || log.includes('🔍')
                  ? 'text-cyan-300'
                  : 'text-slate-300'
              }>
                {log}
              </span>
            </div>
          ))
        )}
        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
