import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { DailyReportResponse, MarketData, MiniReport } from '../types';
import AudioPlayer from './AudioPlayer';
import { Star } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { logger } from '../utils/logger';

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
        logger.error("Failed to load watchlist", e);
        return [];
    }
  });

  // Expanded tickers for detailed analysis
  const [expandedTickers, setExpandedTickers] = useState<Set<string>>(new Set());

  const toggleWatchlist = (ticker: string) => {
    const newWatchlist = watchlist.includes(ticker)
        ? watchlist.filter(t => t !== ticker)
        : [...watchlist, ticker];
    
    setWatchlist(newWatchlist);
    localStorage.setItem('brooks_watchlist', JSON.stringify(newWatchlist));
  };

  const toggleExpanded = (ticker: string) => {
    setExpandedTickers(prev => {
      const next = new Set(prev);
      if (next.has(ticker)) {
        next.delete(ticker);
      } else {
        next.add(ticker);
      }
      return next;
    });
  };

  const safeMarketData = Array.isArray(marketData) ? marketData : [];
  
  // Helper to get market data for a ticker
  const getMarketDataForTicker = (ticker: string): MarketData | undefined => {
    return safeMarketData.find(m => m.ticker === ticker);
  };

  // Helper to extract detailed report section for a ticker
  const getDetailedReportForTicker = (ticker: string): string | null => {
    if (!data.core_tickers_in_depth_markdown) return null;
    // Match markdown section starting with ## TICKER or ### TICKER
    const regex = new RegExp(`(?:##|###)\\s+${ticker}[\\s\\S]*?(?=(?:##|###|$))`, 'i');
    const match = data.core_tickers_in_depth_markdown.match(regex);
    return match ? match[0] : null;
  };
  const topMoversData = safeMarketData
    .sort((a, b) => Math.abs(b.percent_change) - Math.abs(a.percent_change))
    .slice(0, 5)
    .map(d => ({
        ...d,
        color: d.percent_change >= 0 ? '#10b981' : '#ef4444'
    }));

  // Largest movers by volume
  const largestVolumeMovers = [...safeMarketData]
    .sort((a, b) => b.volume - a.volume)
    .slice(0, 10)
    .map(d => ({
      ticker: d.ticker,
      companyName: d.company_name,
      volume: d.volume,
      averageVolume: d.average_volume,
      volumeRatio: d.average_volume > 0 ? (d.volume / d.average_volume) : 0,
      percentChange: d.percent_change,
    }));

  // Largest price changes
  const largestPriceChanges = [...safeMarketData]
    .map(d => ({
      ticker: d.ticker,
      companyName: d.company_name,
      priceChange: d.close - d.previous_close,
      percentChange: d.percent_change,
      close: d.close,
      previousClose: d.previous_close,
    }))
    .sort((a, b) => Math.abs(b.percentChange) - Math.abs(a.percentChange))
    .slice(0, 10);

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
            {/* Largest Movers by Volume Visualization */}
            {largestVolumeMovers.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-300 mb-4">📊 Largest Movers by Volume</h3>
                <div className="h-64 w-full min-w-0">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart data={largestVolumeMovers} margin={{ top: 5, right: 20, left: 5, bottom: 60 }}>
                      <XAxis 
                        dataKey="ticker" 
                        tick={{fill: '#94a3b8', fontSize: 11}} 
                        axisLine={false} 
                        tickLine={false}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis 
                        tick={{fill: '#94a3b8', fontSize: 11}}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                      />
                      <Tooltip 
                        contentStyle={{backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9'}}
                        cursor={{fill: 'rgba(255,255,255,0.05)'}}
                        formatter={(value: any, name: string) => {
                          if (name === 'volume' || name === 'averageVolume') {
                            return [`${(value / 1000000).toFixed(2)}M`, name === 'volume' ? 'Volume' : 'Avg Volume'];
                          }
                          return [value, name];
                        }}
                      />
                      <Legend 
                        wrapperStyle={{color: '#94a3b8', fontSize: '12px'}}
                        iconType="rect"
                      />
                      <Bar dataKey="volume" fill="#10b981" radius={[4, 4, 0, 0]} name="Volume" />
                      <Bar dataKey="averageVolume" fill="#475569" radius={[4, 4, 0, 0]} name="Avg Volume" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
                  {largestVolumeMovers.slice(0, 5).map((mover) => (
                    <div key={mover.ticker} className="bg-slate-800/50 p-2 rounded border border-slate-700">
                      <div className="font-semibold text-emerald-400">{mover.ticker}</div>
                      <div className="text-slate-400">Vol: {mover.volumeRatio.toFixed(2)}x avg</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Largest Price Changes Visualization */}
            {largestPriceChanges.length > 0 && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-slate-300 mb-4">💰 Largest Price Changes</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Dollar Changes */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-400 mb-3">By Dollar Amount</h4>
                    <div className="space-y-2">
                      {[...largestPriceChanges]
                        .sort((a, b) => Math.abs(b.priceChange) - Math.abs(a.priceChange))
                        .slice(0, 5)
                        .map((change) => (
                          <div 
                            key={change.ticker} 
                            className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700"
                          >
                            <div>
                              <div className="font-semibold text-white">{change.ticker}</div>
                              <div className="text-xs text-slate-400">{change.companyName}</div>
                            </div>
                            <div className="text-right">
                              <div className={`font-bold ${change.priceChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                {change.priceChange >= 0 ? '+' : ''}${change.priceChange.toFixed(2)}
                              </div>
                              <div className="text-xs text-slate-500">
                                ${change.previousClose.toFixed(2)} → ${change.close.toFixed(2)}
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                  
                  {/* Percentage Changes */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-400 mb-3">By Percentage</h4>
                    <div className="space-y-2">
                      {largestPriceChanges.slice(0, 5).map((change) => (
                        <div 
                          key={change.ticker} 
                          className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700"
                        >
                          <div>
                            <div className="font-semibold text-white">{change.ticker}</div>
                            <div className="text-xs text-slate-400">{change.companyName}</div>
                          </div>
                          <div className="text-right">
                            <div className={`font-bold ${change.percentChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {change.percentChange >= 0 ? '+' : ''}{change.percentChange.toFixed(2)}%
                            </div>
                            <div className="text-xs text-slate-500">
                              ${change.previousClose.toFixed(2)} → ${change.close.toFixed(2)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Chart Section */}
            {topMoversData.length > 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Volume Leaders vs Avg</h3>
                <div className="h-48 w-full min-w-0">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <BarChart data={topMoversData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
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
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-sm text-center">
                <div className="text-4xl mb-3">📈</div>
                <h3 className="text-sm font-semibold text-slate-400 mb-1">No Market Data Available</h3>
                <p className="text-xs text-slate-500">Market data is required to display volume charts.</p>
              </div>
            )}

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
                                aria-label={isWatched ? `Remove ${report.ticker} from watchlist` : `Add ${report.ticker} to watchlist`}
                                aria-pressed={isWatched}
                                title={isWatched ? "Remove from Watchlist" : "Add to Watchlist"}
                             >
                                <Star size={16} fill={isWatched ? "currentColor" : "none"} aria-hidden="true" />
                             </button>
                          </div>
                          <p className="text-xs text-slate-400 truncate max-w-[150px]">{report.company_name}</p>
                        </div>
                        <div className="bg-slate-800 px-2 py-1 rounded text-xs text-emerald-400 font-mono">
                            {report.section_title.split(':')[0]}
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        {/* Market Data Card */}
                        {(() => {
                          const marketInfo = getMarketDataForTicker(report.ticker);
                          return marketInfo ? (
                            <div className="grid grid-cols-2 gap-2 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                              <div>
                                <span className="text-xs text-slate-500">Price</span>
                                <p className="text-sm font-semibold text-white">${marketInfo.close.toFixed(2)}</p>
                              </div>
                              <div>
                                <span className="text-xs text-slate-500">Change</span>
                                <p className={`text-sm font-semibold ${marketInfo.percent_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                  {marketInfo.percent_change >= 0 ? '+' : ''}{marketInfo.percent_change.toFixed(2)}%
                                </p>
                              </div>
                              <div>
                                <span className="text-xs text-slate-500">Volume</span>
                                <p className="text-sm font-semibold text-slate-300">
                                  {(marketInfo.volume / 1000000).toFixed(2)}M
                                </p>
                              </div>
                              <div>
                                <span className="text-xs text-slate-500">Market Cap</span>
                                <p className="text-sm font-semibold text-slate-300">{marketInfo.market_cap}</p>
                              </div>
                            </div>
                          ) : null;
                        })()}

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

                        {/* Expandable Detailed Analysis */}
                        {(() => {
                          const detailedReport = getDetailedReportForTicker(report.ticker);
                          const isExpanded = expandedTickers.has(report.ticker);
                          
                          return detailedReport ? (
                            <div>
                              <button
                                onClick={() => toggleExpanded(report.ticker)}
                                className="text-xs font-bold text-emerald-500 hover:text-emerald-400 uppercase mb-2 flex items-center gap-1 transition-colors"
                                aria-label={isExpanded ? 'Collapse detailed analysis' : 'Expand detailed analysis'}
                                aria-expanded={isExpanded}
                              >
                                <span>{isExpanded ? '▼' : '▶'}</span> Detailed Analysis
                              </button>
                              {isExpanded && (
                                <div className="mt-2 p-3 bg-slate-800/30 rounded-lg border border-slate-700 prose prose-invert prose-xs max-w-none">
                                  <ReactMarkdown>{detailedReport}</ReactMarkdown>
                                </div>
                              )}
                            </div>
                          ) : null;
                        })()}

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
                <div className="col-span-full">
                  <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-12 border border-slate-700 text-center shadow-lg">
                    <div className="max-w-md mx-auto space-y-4">
                      <div className="text-6xl mb-4">📊</div>
                      <h3 className="text-xl font-bold text-slate-300">No Ticker Reports Available</h3>
                      <p className="text-slate-400">
                        The report was generated but no individual ticker reports were included. 
                        This may happen if the market data or inputs were incomplete.
                      </p>
                      <div className="mt-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                        <p className="text-sm text-slate-400">
                          <strong className="text-slate-300">Tip:</strong> Ensure you provide market data with ticker information, 
                          or check that the AI was able to generate ticker-specific insights.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB: DEEP DIVE */}
        {activeTab === 'deep-dive' && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
            {data.core_tickers_in_depth_markdown && data.core_tickers_in_depth_markdown.trim() ? (
              <div className="prose prose-invert prose-slate max-w-none prose-headings:text-emerald-400 prose-a:text-emerald-400 hover:prose-a:text-emerald-300">
                <ReactMarkdown>{data.core_tickers_in_depth_markdown}</ReactMarkdown>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-5xl mb-4">🔍</div>
                <h3 className="text-lg font-semibold text-slate-300 mb-2">Deep Dive Content Not Available</h3>
                <p className="text-slate-400">The deep dive section was not included in this report.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB: FULL NARRATIVE */}
        {activeTab === 'full' && (
          <div className="max-w-4xl mx-auto bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
            {data.report_markdown && data.report_markdown.trim() ? (
              <div className="prose prose-invert prose-slate max-w-none prose-headings:text-emerald-400">
                <ReactMarkdown>{data.report_markdown}</ReactMarkdown>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-5xl mb-4">📝</div>
                <h3 className="text-lg font-semibold text-slate-300 mb-2">Full Narrative Not Available</h3>
                <p className="text-slate-400">The full narrative report was not included in this response.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportView;