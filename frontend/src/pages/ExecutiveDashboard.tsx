import { useEffect, useState } from 'react';
import { getScenarios, getScenarioDetails } from '../services/api';
import { loadEnterpriseCache, EnterpriseCache } from '../utils/enterpriseCache';
import { AlertTriangle, TrendingDown, Clock, Zap, CheckCircle, ArrowRight, Database } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  Cell, Legend,
} from 'recharts';

// ── Custom tooltip ────────────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label, formatter }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-3 py-2 text-xs">
      <p className="font-semibold text-gray-700 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {formatter ? formatter(p.value) : p.value}
        </p>
      ))}
    </div>
  );
};

// ── Color palettes ─────────────────────────────────────────────────────────────
const CAT_COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ExecutiveDashboard() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const cache: EnterpriseCache | null = loadEnterpriseCache();

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await getScenarios();
      setScenarios(data);
      if (data.length > 0) {
        loadScenarioDetails(data[0].scenario_id);
      }
    } catch (error) {
      console.error('Error loading scenarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadScenarioDetails = async (scenarioId: string) => {
    try {
      const details = await getScenarioDetails(scenarioId);
      setSelectedScenario(details);
    } catch (error) {
      console.error('Error loading scenario details:', error);
    }
  };

  const getUrgencyConfig = (urgency: string) => {
    const configs: Record<string, { bg: string; text: string; ring: string; dot: string }> = {
      Critical: { bg: 'bg-red-50', text: 'text-red-700', ring: 'ring-red-200', dot: 'bg-red-500' },
      High:     { bg: 'bg-amber-50', text: 'text-amber-700', ring: 'ring-amber-200', dot: 'bg-amber-500' },
      Medium:   { bg: 'bg-blue-50', text: 'text-blue-700', ring: 'ring-blue-200', dot: 'bg-blue-500' },
      Low:      { bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200', dot: 'bg-emerald-500' },
    };
    return configs[urgency] || { bg: 'bg-gray-50', text: 'text-gray-700', ring: 'ring-gray-200', dot: 'bg-gray-400' };
  };

  const getComplexityColor = (complexity: string) => {
    if (complexity === 'High') return 'text-red-600 bg-red-50';
    if (complexity === 'Medium') return 'text-amber-600 bg-amber-50';
    return 'text-emerald-600 bg-emerald-50';
  };

  // ── Chart data derived from cache ──────────────────────────────────────────
  const revenueData = cache?.categories.map(c => ({
    name: c.product_category,
    Revenue: Math.round(c.total_revenue / 1000),
    'Lost Sales': Math.round(c.lost_sales_value / 1000),
  })) ?? [];

  const riskData = cache?.categories.map(c => ({
    name: c.product_category,
    Stockout: parseFloat((c.stockout_rate * 100).toFixed(1)),
    Overstock: parseFloat((c.overstock_rate * 100).toFixed(1)),
    Fulfillment: parseFloat((c.fulfillment_rate * 100).toFixed(1)),
  })) ?? [];

  const radarData = cache ? [
    { metric: 'Fulfillment', value: parseFloat((cache.aggregate.fulfillment_rate * 100).toFixed(1)) },
    { metric: 'Seller Quality', value: parseFloat((cache.aggregate.avg_seller_quality * 100).toFixed(1)) },
    { metric: 'Promo Rate', value: parseFloat((cache.aggregate.promotion_rate * 100).toFixed(1)) },
    { metric: 'Stock Health', value: parseFloat(((1 - cache.aggregate.overstock_rate) * 100).toFixed(1)) },
    { metric: 'Supply Reliability', value: parseFloat(((1 - cache.aggregate.stockout_rate) * 100).toFixed(1)) },
  ] : [];

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-gray-200 rounded-xl w-56" />
        <div className="bg-white rounded-2xl h-48 shadow-card" />
        <div className="bg-white rounded-2xl h-48 shadow-card" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Executive Dashboard</h2>
        <p className="mt-0.5 text-sm text-gray-500">
          Critical insights and decision support for retail risk management
        </p>
      </div>

      {cache ? (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
              <p className="text-xs font-semibold text-indigo-500 uppercase tracking-wide mb-1">Total Revenue</p>
              <p className="text-3xl font-bold text-indigo-700">${(cache.aggregate.total_revenue / 1_000_000).toFixed(1)}M</p>
              <p className="text-xs text-gray-400 mt-1">{cache.aggregate.unique_stores} stores · {cache.aggregate.unique_categories} categories</p>
            </div>
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
              <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-1">Fulfillment Rate</p>
              <p className="text-3xl font-bold text-emerald-700">{(cache.aggregate.fulfillment_rate * 100).toFixed(1)}%</p>
              <div className="mt-2 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${cache.aggregate.fulfillment_rate * 100}%` }} />
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
              <p className="text-xs font-semibold text-red-500 uppercase tracking-wide mb-1">Stockout Rate</p>
              <p className="text-3xl font-bold text-red-600">{(cache.aggregate.stockout_rate * 100).toFixed(1)}%</p>
              <p className="text-xs text-gray-400 mt-1">Lost sales: ${(cache.aggregate.total_lost_sales_value / 1000).toFixed(0)}K</p>
            </div>
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
              <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">Holding Cost</p>
              <p className="text-3xl font-bold text-amber-700">${(cache.aggregate.total_holding_cost / 1_000).toFixed(0)}K</p>
              <p className="text-xs text-gray-400 mt-1">Overstock rate: {(cache.aggregate.overstock_rate * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Revenue vs Lost Sales by category */}
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900">Revenue vs Lost Sales by Category</h3>
                <p className="text-xs text-gray-400 mt-0.5">Values in thousands (K)</p>
              </div>
              <div className="p-4">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={revenueData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={v => `$${v}K`} />
                    <Tooltip content={<ChartTooltip formatter={(v: number) => `$${v}K`} />} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="Revenue" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Lost Sales" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Stockout vs Overstock rate by category */}
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900">Stockout & Overstock Rates</h3>
                <p className="text-xs text-gray-400 mt-0.5">Percentage by category</p>
              </div>
              <div className="p-4">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={riskData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} tickFormatter={v => `${v}%`} />
                    <Tooltip content={<ChartTooltip formatter={(v: number) => `${v}%`} />} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="Stockout" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Overstock" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Fulfillment + Radar row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fulfillment per category bar */}
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900">Fulfillment Rate by Category</h3>
              </div>
              <div className="p-5 space-y-3">
                {cache.categories.map((cat, i) => (
                  <div key={cat.product_category}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{cat.product_category}</span>
                      <span className={`text-sm font-bold ${cat.fulfillment_rate >= 0.85 ? 'text-emerald-600' : cat.fulfillment_rate >= 0.7 ? 'text-amber-600' : 'text-red-600'}`}>
                        {(cat.fulfillment_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${cat.fulfillment_rate * 100}%`,
                          backgroundColor: cat.fulfillment_rate >= 0.85 ? '#10b981' : cat.fulfillment_rate >= 0.7 ? '#f59e0b' : '#ef4444',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Operations Health Radar */}
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900">Operations Health</h3>
                <p className="text-xs text-gray-400 mt-0.5">Higher is better across all dimensions</p>
              </div>
              <div className="p-4 flex items-center justify-center">
                <ResponsiveContainer width="100%" height={240}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#6b7280' }} />
                    <Radar name="Fleet" dataKey="value" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.15} strokeWidth={2} />
                    <Tooltip content={<ChartTooltip formatter={(v: number) => `${v}%`} />} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Category table + footer */}
          <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-indigo-50">
                <Database className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">Dataset Overview — {cache.fileName}</h3>
                <p className="text-xs text-gray-400">{cache.recordsCount.toLocaleString()} records · uploaded {new Date(cache.savedAt).toLocaleDateString()}</p>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50/80 border-b border-gray-100">
                    <th className="text-left text-xs font-semibold text-gray-500 py-3 px-6">Category</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-4">Revenue</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-4">Fulfillment</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-4">Stockout</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-4">Overstock</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-4">Avg Demand</th>
                    <th className="text-right text-xs font-semibold text-gray-500 py-3 px-6">Lost Sales</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {cache.categories.map((cat, idx) => (
                    <tr key={cat.product_category} className={`hover:bg-indigo-50/20 transition-colors ${idx % 2 === 0 ? '' : 'bg-gray-50/30'}`}>
                      <td className="py-3 px-6 font-semibold text-gray-800">{cat.product_category}</td>
                      <td className="py-3 px-4 text-right text-gray-600">${(cat.total_revenue / 1_000).toFixed(0)}K</td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-medium ${cat.fulfillment_rate >= 0.85 ? 'text-emerald-600' : cat.fulfillment_rate >= 0.7 ? 'text-amber-600' : 'text-red-600'}`}>
                          {(cat.fulfillment_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-medium ${cat.stockout_rate <= 0.1 ? 'text-emerald-600' : cat.stockout_rate <= 0.25 ? 'text-amber-600' : 'text-red-600'}`}>
                          {(cat.stockout_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-medium ${cat.overstock_rate <= 0.1 ? 'text-emerald-600' : cat.overstock_rate <= 0.25 ? 'text-amber-600' : 'text-red-600'}`}>
                          {(cat.overstock_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">{cat.avg_demand.toFixed(0)}</td>
                      <td className="py-3 px-6 text-right text-red-500 font-medium">${(cat.lost_sales_value / 1_000).toFixed(0)}K</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-6 py-3 border-t border-gray-100 flex flex-wrap gap-4 text-xs text-gray-500">
              <span><span className="font-semibold text-gray-700">{cache.aggregate.unique_stores}</span> stores</span>
              <span><span className="font-semibold text-gray-700">{cache.aggregate.unique_categories}</span> categories</span>
              <span><span className="font-semibold text-gray-700">{cache.aggregate.unique_regions}</span> regions</span>
              <span><span className="font-semibold text-gray-700">{cache.aggregate.unique_products}</span> products</span>
              {cache.aggregate.date_range && (
                <span>{cache.aggregate.date_range.start} – {cache.aggregate.date_range.end} ({cache.aggregate.date_range.days}d)</span>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 py-16 text-center">
          <div className="w-14 h-14 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Database className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-sm font-medium text-gray-500">No dataset uploaded yet</p>
          <p className="text-xs text-gray-400 mt-1">Upload an Enterprise dataset to see KPIs, charts, and category insights here</p>
        </div>
      )}

      {selectedScenario?.summary && (
        <>
          {/* Executive Summary Card */}
          <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
            <div className="h-1 w-full" style={{ background: 'linear-gradient(90deg, #4f46e5, #7c3aed, #db2777)' }} />
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #fef2f2, #fee2e2)' }}>
                    <AlertTriangle className="h-6 w-6 text-red-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {selectedScenario.scenario.scenario_type.replace(/_/g, ' ')}
                    </h3>
                    <p className="text-xs text-gray-400 mt-0.5 font-mono">
                      ID: {selectedScenario.scenario.scenario_id.slice(0, 8)}...
                    </p>
                  </div>
                </div>
                {(() => {
                  const cfg = getUrgencyConfig(selectedScenario.summary.urgency_level);
                  return (
                    <span className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ring-1 ${cfg.bg} ${cfg.text} ${cfg.ring}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                      <span>{selectedScenario.summary.urgency_level} Urgency</span>
                    </span>
                  );
                })()}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-xl p-4 border border-red-100 bg-red-50/50">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-7 h-7 bg-red-100 rounded-lg flex items-center justify-center">
                      <TrendingDown className="h-3.5 w-3.5 text-red-600" />
                    </div>
                    <h4 className="text-xs font-semibold text-red-800 uppercase tracking-wide">Revenue Risk</h4>
                  </div>
                  <p className="text-sm text-red-700 leading-relaxed">{selectedScenario.summary.revenue_risk}</p>
                </div>
                <div className="rounded-xl p-4 border border-indigo-100 bg-indigo-50/50">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-7 h-7 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <Zap className="h-3.5 w-3.5 text-indigo-600" />
                    </div>
                    <h4 className="text-xs font-semibold text-indigo-800 uppercase tracking-wide">Market Reason</h4>
                  </div>
                  <p className="text-sm text-indigo-700 leading-relaxed">{selectedScenario.summary.market_reason}</p>
                </div>
                <div className="rounded-xl p-4 border border-amber-100 bg-amber-50/50">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
                      <Clock className="h-3.5 w-3.5 text-amber-600" />
                    </div>
                    <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wide">Urgency</h4>
                  </div>
                  <p className="text-sm text-amber-700 leading-relaxed">
                    {selectedScenario.summary.urgency_level} — Immediate action required
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Impact Analysis */}
          {selectedScenario.impact && (
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="text-base font-semibold text-gray-900">Impact Analysis</h3>
              </div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">Overall Propagation Score</span>
                  <span className="text-2xl font-bold text-red-600">
                    {selectedScenario.impact.overall_score}<span className="text-sm font-medium text-gray-400">/10</span>
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2.5 mb-6">
                  <div
                    className="h-2.5 rounded-full transition-all"
                    style={{
                      width: `${(selectedScenario.impact.overall_score / 10) * 100}%`,
                      background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                    }}
                  />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(selectedScenario.impact.function_impacts).map(([func, impact]: [string, any]) => {
                    const pct = (impact / 10) * 100;
                    const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981';
                    return (
                      <div key={func} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <p className="text-xs font-medium text-gray-500 capitalize mb-2">{func}</p>
                        <p className="text-xl font-bold text-gray-900 mb-2">{impact.toFixed(1)}</p>
                        <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Mitigation Strategies */}
          {selectedScenario.strategies && selectedScenario.strategies.length > 0 && (
            <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-base font-semibold text-gray-900">Recommended Actions</h3>
                <span className="text-xs text-gray-400">{selectedScenario.strategies.length} strategies</span>
              </div>
              <div className="p-4 space-y-3">
                {selectedScenario.strategies.map((strategy: any, index: number) => (
                  <div
                    key={strategy.strategy_id}
                    className="flex items-start space-x-4 p-4 rounded-xl border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/20 transition-all group"
                  >
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 text-indigo-600"
                      style={{ background: 'linear-gradient(135deg, #eef2ff, #e0e7ff)' }}>
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
                        {strategy.strategy_name}
                      </h4>
                      <p className="text-sm text-gray-500 mt-1 leading-relaxed">{strategy.description}</p>
                      <div className="flex flex-wrap items-center gap-3 mt-3">
                        <div className="flex items-center space-x-1.5">
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                          <span className="text-xs font-medium text-gray-600">
                            {(strategy.effectiveness_score * 100).toFixed(0)}% effective
                          </span>
                        </div>
                        <div className="flex items-center space-x-1.5">
                          <Clock className="h-3.5 w-3.5 text-gray-400" />
                          <span className="text-xs text-gray-500">{strategy.timeline_days} days</span>
                        </div>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getComplexityColor(strategy.implementation_complexity)}`}>
                          {strategy.implementation_complexity} complexity
                        </span>
                        {strategy.cost_estimate && (
                          <span className="text-xs text-gray-500 font-medium">
                            ${strategy.cost_estimate.toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-1" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!selectedScenario && !loading && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 py-16 text-center">
          <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="h-8 w-8 text-gray-300" />
          </div>
          <h3 className="text-base font-semibold text-gray-700 mb-1">No Simulation Results Yet</h3>
          <p className="text-sm text-gray-400">Go to the Analyst Dashboard and run a simulation to see scenario insights here</p>
        </div>
      )}
    </div>
  );
}
