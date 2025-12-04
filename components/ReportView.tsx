import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { DailyReportResponse, MarketData, MiniReport } from '../types';
import AudioPlayer from './AudioPlayer';
import { ArrowUpRight, ArrowDownRight, Activity, BarChart2, Layers, Star } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface ReportViewProps {
  data: DailyReportResponse;
  marketData: MarketData[];
}

const ReportView: React.FC<ReportViewProps> = ({ data, marketData }) => {
  const [activeTab, setActiveTab] = useState<'brief' | 'deep-dive' | 'full'>('brief');
  
  // Watchlist State Logic
  const [watchlist, setWatchlist] = useState<string[]>(() => {
    try {
        const saved = localStorage.getItem('brooks_watchlist');
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error("Failed to load watchlist", e);
        return [];
    }
  });

  const toggleWatchlist = (ticker: string) => {
    const newWatchlist = watchlist.includes(ticker)
        ? watchlist.filter(t => t !== ticker)
        : [...watchlist, ticker];
    
    setWatchlist(newWatchlist);
    localStorage.setItem('brooks_watchlist', JSON.stringify(newWatchlist));
  };

  const safeMarketData = Array.isArray(marketData) ? marketData : [];
  const topMoversData = safeMarketData
    .sort((a, b) => Math.abs(b.percent_change) - Math.abs(a.percent_change))
    .slice(0, 5)
    .map(d => ({
        ...d,
        color: d.percent_change >= 0 ? '#10b981' : '#ef4444'
    }));

  return (
    <div className="flex flex-col h-full bg-slate-950 overflow-hidden">
      {/* Header & Controls */}
      <div className="p-6 border-b border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/50">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Daily Intelligence</h2>
          <p className="text-sm text-slate-400">Data Center Sector Report</p>
        </div>
        <div className="w-full md:w-auto">
             <AudioPlayer text={data.audio_report} />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/30">
        <button
          onClick={() => setActiveTab('brief')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'brief'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Top Movers
        </button>
        <button
          onClick={() => setActiveTab('deep-dive')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'deep-dive'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Deep Dive (Core)
        </button>
        <button
          onClick={() => setActiveTab('full')}
          className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === 'full'
              ? 'border-emerald-500 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Full Narrative
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        
        {/* TAB: TOP MOVERS (BRIEF) */}
        {activeTab === 'brief' && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Chart Section */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Volume Leaders vs Avg</h3>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={topMoversData}>
                            <XAxis dataKey="ticker" tick={{fill: '#94a3b8', fontSize: 10}} axisLine={false} tickLine={false} />
                            <Tooltip 
                                contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}}
                                cursor={{fill: 'rgba(255,255,255,0.05)'}}
                            />
                            <Bar dataKey="volume" fill="#10b981" radius={[4, 4, 0, 0]} />
                             <Bar dataKey="average_volume" fill="#334155" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {data.reports && data.reports.length > 0 ? (
                data.reports?.map((report: MiniReport, idx: number) => {
                  const isWatched = watchlist.includes(report.ticker);
                  return (
                    <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors shadow-lg shadow-black/20 group">
                      <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-3">
                        <div>
                          <div className="flex items-center gap-2">
                             <h3 className="text-xl font-bold text-white">{report.ticker}</h3>
                             <button
                                onClick={() => toggleWatchlist(report.ticker)}
                                className={`transition-all duration-200 p-1 rounded hover:bg-slate-800 ${isWatched ? 'text-yellow-400' : 'text-slate-600 hover:text-yellow-400'}`}
                                title={isWatched ? "Remove from Watchlist" : "Add to Watchlist"}
                             >
                                <Star size={16} fill={isWatched ? "currentColor" : "none"} />
                             </button>
                          </div>
                          <p className="text-xs text-slate-400 truncate max-w-[150px]">{report.company_name}</p>
                        </div>
                        <div className="bg-slate-800 px-2 py-1 rounded text-xs text-emerald-400 font-mono">
                            {report.section_title.split(':')[0]}
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-1">Snapshot</h4>
                            <p className="text-sm text-slate-200 leading-relaxed">{report.snapshot}</p>
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-1">Catalyst</h4>
                            <p className="text-sm text-slate-300 leading-relaxed">{report.catalyst_and_context}</p>
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-emerald-700/80 uppercase mb-1">Trading Lens</h4>
                            <div className="bg-emerald-950/20 border-l-2 border-emerald-600 pl-3 py-1">
                                <p className="text-sm text-emerald-100/90 italic leading-relaxed">{report.day_trading_lens}</p>
                            </div>
                        </div>
                        <div>
                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Watch Next</h4>
                            <ul className="space-y-1">
                                {report.watch_next_bullets && Array.isArray(report.watch_next_bullets) ? (
                                    report.watch_next_bullets?.map((bullet, i) => (
                                        <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                                            <span className="mt-1 w-1 h-1 rounded-full bg-emerald-500 shrink-0"></span>
                                            {bullet}
                                        </li>
                                    ))
                                ) : (
                                    <li className="text-xs text-slate-500">No watch items available.</li>
                                )}
                            </ul>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="col-span-full text-center py-10 text-slate-500">
                  <p>No ticker reports generated. Please check inputs.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB: DEEP DIVE */}
        {activeTab === 'deep-dive' && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
             <div className="prose prose-invert prose-slate max-w-none prose-headings:text-emerald-400 prose-a:text-emerald-400 hover:prose-a:text-emerald-300">
                <ReactMarkdown>{data.core_tickers_in_depth_markdown}</ReactMarkdown>
             </div>
          </div>
        )}

        {/* TAB: FULL NARRATIVE */}
        {activeTab === 'full' && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="prose prose-invert prose-slate max-w-none prose-headings:text-emerald-400">
                <ReactMarkdown>{data.report_markdown}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportView;