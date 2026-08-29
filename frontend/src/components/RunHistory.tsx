import React from 'react';
import { Play, RotateCcw, Clock, ArrowRight, ExternalLink } from 'lucide-react';
import { Run } from '../types';

interface RunHistoryProps {
  runs: Run[];
  onSelectRun: (runId: string) => void;
  onReplayRun: (runId: string) => void;
}

export default function RunHistory({ runs, onSelectRun, onReplayRun }: RunHistoryProps) {
  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-black text-white">Venture Run History</h2>
          <p className="text-sm text-slate-400 font-mono">Persisted records of all autonomous pipeline runs</p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-12 text-center">
          <p className="text-slate-500 font-mono text-sm">No historical runs recorded yet. Launch your first venture above!</p>
        </div>
      ) : (
        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl overflow-hidden shadow-2xl">
          <div className="divide-y divide-slate-800/60">
            {runs.map((run) => (
              <div
                key={run.id}
                className="p-6 hover:bg-slate-800/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-xs text-yellow-400 bg-yellow-950/40 px-2.5 py-0.5 rounded-full border border-yellow-800/50">
                      {run.id}
                    </span>
                    <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-full ${
                      run.status === 'completed' 
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' 
                        : run.status === 'failed'
                        ? 'bg-rose-950/60 text-rose-400 border border-rose-800'
                        : 'bg-cyan-950/60 text-cyan-400 border border-cyan-800 animate-pulse'
                    }`}>
                      {run.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-slate-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(run.started_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-white tracking-tight">
                    {run.product_name ? `${run.product_name} — ${run.tagline || ''}` : run.idea}
                  </h4>
                  <p className="text-xs text-slate-400 line-clamp-1 italic font-mono">
                    "{run.idea}"
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onReplayRun(run.id)}
                    className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Replay</span>
                  </button>
                  <button
                    onClick={() => onSelectRun(run.id)}
                    className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-colors"
                  >
                    <span>View Detail</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
