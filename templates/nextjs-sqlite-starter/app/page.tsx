'use client';

import React, { useState } from 'react';
import PlaceholderFeature from '../components/features/PlaceholderFeature';

export default function Home() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('loading');
    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus('success');
        setMessage(data.message || 'Joined waitlist!');
        setEmail('');
      } else {
        setStatus('error');
        setMessage(data.error || 'Failed to join waitlist');
      }
    } catch (err: any) {
      setStatus('error');
      setMessage(err.message || 'Network error');
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-between p-6 md:p-24 selection:bg-cyan-500 selection:text-white">
      {/* <!-- FOUNDER0:NAVBAR_START --> */}
      <header className="w-full max-w-6xl flex justify-between items-center py-4 mb-16 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-cyan-500/20">
            F0
          </div>
          <span className="font-extrabold text-xl tracking-tight text-white">FOUNDER-0 MVP</span>
        </div>
        <a 
          href="#signup" 
          className="text-xs font-semibold px-4 py-2 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all font-mono"
        >
          Early Access
        </a>
      </header>
      {/* <!-- FOUNDER0:NAVBAR_END --> */}

      {/* <!-- FOUNDER0:HERO_START --> */}
      <section className="w-full max-w-4xl text-center flex flex-col items-center mb-24">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-6">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
          Autonomous MVP Scaffold
        </div>
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          Next Generation <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">Autonomous MVP</span>
        </h1>
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed">
          Generated automatically by FOUNDER-0 from a single prompt. Solving market whitespace with verifiable code.
        </p>
      </section>
      {/* <!-- FOUNDER0:HERO_END --> */}

      {/* <!-- FOUNDER0:FEATURES_START --> */}
      <section className="w-full max-w-6xl mb-24">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">Core Product Capabilities</h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto">Engineered to eliminate specific user friction points identified in competitive market recon.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PlaceholderFeature 
            title="Intelligent Core" 
            description="Autonomous feature execution addressing gaps found in competitor reviews." 
          />
          <PlaceholderFeature 
            title="Realtime Sync" 
            description="Instant state reconciliation across distributed user actions." 
          />
          <PlaceholderFeature 
            title="Frictionless Onboarding" 
            description="Zero-config setup with embedded self-healing reliability." 
          />
        </div>
      </section>
      {/* <!-- FOUNDER0:FEATURES_END --> */}

      {/* <!-- FOUNDER0:SIGNUP_START --> */}
      <section id="signup" className="w-full max-w-2xl bg-gradient-to-b from-slate-900 to-slate-900/80 border border-slate-800 rounded-3xl p-8 md:p-12 text-center shadow-2xl relative overflow-hidden mb-16">
        <div className="absolute inset-0 bg-cyan-500/5 blur-3xl rounded-full"></div>
        <div className="relative z-10">
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-3">Get Early Access</h3>
          <p className="text-slate-400 text-sm mb-8">Join the exclusive early adopter waitlist.</p>
          
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your work email..." 
              required
              className="flex-1 px-4 py-3 rounded-xl bg-slate-950/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 text-sm transition-all"
            />
            <button 
              type="submit" 
              disabled={status === 'loading'}
              className="px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition-all whitespace-nowrap disabled:opacity-50"
            >
              {status === 'loading' ? 'Joining...' : 'Join Waitlist'}
            </button>
          </form>

          {message && (
            <p className={`mt-4 text-xs font-mono ${status === 'success' ? 'text-emerald-400' : 'text-rose-400'}`}>
              {message}
            </p>
          )}
        </div>
      </section>
      {/* <!-- FOUNDER0:SIGNUP_END --> */}

      {/* <!-- FOUNDER0:FOOTER_START --> */}
      <footer className="w-full max-w-6xl py-8 border-t border-slate-900 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 font-mono">
        <div>© 2026 FOUNDER-0 Autonomous Systems. All rights reserved.</div>
        <div className="mt-2 sm:mt-0 flex gap-4">
          <span>Powered by Daytona</span>
          <span>•</span>
          <span>Nosana Inference</span>
        </div>
      </footer>
      {/* <!-- FOUNDER0:FOOTER_END --> */}
    </main>
  );
}
