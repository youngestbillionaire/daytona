import React, { useEffect, useRef, useState } from 'react';
import { Network, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';
import { GraphData, GraphNode, GraphEdge } from '../types';

interface KnowledgeGraphProps {
  graphData: GraphData;
}

const TYPE_COLORS: Record<string, string> = {
  Idea: '#38bdf8',         // Sky Blue
  Competitor: '#a855f7',   // Purple
  Feature: '#10b981',      // Emerald Green
  Complaint: '#f43f5e',    // Rose Red
  PricingTier: '#f59e0b',  // Amber
  Node: '#94a3b8'
};

export default function KnowledgeGraph({ graphData }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const width = canvas.width;
    const height = canvas.height;

    // Build positions for nodes
    const nodePositions: Record<string, { x: number; y: number; vx: number; vy: number }> = {};
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];

    nodes.forEach((node, idx) => {
      const angle = (idx / Math.max(1, nodes.length)) * Math.PI * 2;
      const radius = node.type === 'Idea' ? 0 : (node.type === 'Competitor' ? 90 : 180);
      nodePositions[node.id] = {
        x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 20,
        y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 20,
        vx: 0,
        vy: 0
      };
    });

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Apply zoom & center transform
      ctx.save();
      ctx.translate(width / 2, height / 2);
      ctx.scale(zoom, zoom);
      ctx.translate(-width / 2, -height / 2);

      // Draw Edges
      edges.forEach(edge => {
        const src = nodePositions[edge.source];
        const tgt = nodePositions[edge.target];
        if (src && tgt) {
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(tgt.x, tgt.y);
          ctx.strokeStyle = 'rgba(71, 85, 105, 0.4)';
          ctx.lineWidth = 1.5;
          ctx.stroke();

          // Draw relationship tag in middle
          const midX = (src.x + tgt.x) / 2;
          const midY = (src.y + tgt.y) / 2;
          ctx.fillStyle = '#64748b';
          ctx.font = '8px "JetBrains Mono"';
          ctx.fillText(edge.relationship, midX - 10, midY - 4);
        }
      });

      // Draw Nodes
      nodes.forEach(node => {
        const pos = nodePositions[node.id];
        if (!pos) return;

        const color = TYPE_COLORS[node.type] || '#38bdf8';
        const radius = node.type === 'Idea' ? 16 : 10;

        // Outer glow
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius + 4, 0, Math.PI * 2);
        ctx.fillStyle = `${color}22`;
        ctx.fill();

        // Core node circle
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Node label
        ctx.fillStyle = '#f8fafc';
        ctx.font = '10px "Plus Jakarta Sans", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label.slice(0, 18), pos.x, pos.y + radius + 12);
      });

      ctx.restore();
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [graphData, zoom]);

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-3xl p-5 shadow-2xl flex flex-col h-full relative overflow-hidden">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Network className="w-4 h-4 text-cyan-400" />
          <h3 className="font-extrabold text-sm text-white">Neo4j Opportunity Knowledge Graph</h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400">
            {graphData.node_count || 0} Nodes • {graphData.edge_count || 0} Relations
          </span>
          <button onClick={() => setZoom(z => Math.min(1.8, z + 0.15))} className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => setZoom(z => Math.max(0.5, z - 0.15))} className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative flex items-center justify-center min-h-[280px]">
        {graphData.nodes?.length === 0 ? (
          <div className="text-slate-500 font-mono text-xs italic text-center">
            Graph population begins at Stage 4 (OPPORTUNITY_GRAPH)...
          </div>
        ) : (
          <canvas ref={canvasRef} width={580} height={320} className="w-full h-full rounded-2xl cursor-grab active:cursor-grabbing" />
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-3 border-t border-slate-800/60 text-[11px] font-mono text-slate-400">
        <div className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#38bdf8]"></span><span>Idea</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#a855f7]"></span><span>Competitor</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#10b981]"></span><span>Feature</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#f43f5e]"></span><span>Complaint</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]"></span><span>Pricing</span></div>
      </div>
    </div>
  );
}
