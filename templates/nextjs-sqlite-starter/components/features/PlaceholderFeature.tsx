'use client';

import React, { useState } from 'react';

export interface FeatureProps {
  title?: string;
  description?: string;
}

export default function PlaceholderFeature({
  title = "AI Automation",
  description = "Intelligently automates the workflow to resolve market pain points seamlessly."
}: FeatureProps) {
  const [active, setActive] = useState(false);

  return (
    <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition-all">
      <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center font-bold text-xl mb-4">
        ⚡
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
      <p className="text-slate-600 text-sm leading-relaxed mb-4">{description}</p>
      <button 
        onClick={() => setActive(!active)}
        className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
      >
        {active ? 'Active Demo' : 'Try Interactive Demo'}
      </button>
    </div>
  );
}
