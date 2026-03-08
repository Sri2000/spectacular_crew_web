import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2, DollarSign, CheckCircle2, AlertCircle, Package,
  TrendingDown, Store, Star, Upload, RefreshCw, Database,
  ChevronRight, ArrowUpDown,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, ZAxis,
} from 'recharts';
import { loadEnterpriseCache, EnterpriseCache } from '../utils/enterpriseCache';
import { StoreCategoryStat } from '../services/api';

// ── Formatters ────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n);

const fmtCurrency = (n: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const fmtPct = (r: number) => (r * 100).toFixed(1) + '%';

const TOOLTIP_STYLE = {
  borderRadius: '12px',
  border: '1px solid #e2e8f0',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  fontSize: '12px',
};

// ── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({
  icon: Icon, iconBg, iconColor, label, value, badge, badgeColor,
}: {
  icon: typeof Store; iconBg: string; iconColor: string;
  label: string; value: string | number; badge?: string; badgeColor?: string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5 hover:shadow-card-hover transition-all duration-200">
      <div className="flex items-start justify-between">
        <div className={`w-11 h-11 ${iconBg} rounded-xl flex items-center justify-center`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
        {badge && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${badgeColor ?? 'bg-gray-50 text-gray-400'}`}>
            {badge}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-gray-900 mt-4 truncate">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

// ── Store Fleet Card (drill-through) ─────────────────────────────────────────

interface StoreSummary {
  storeId: string;
  region: string;
  totalRevenue: number;
  avgStockoutRate: number;
  avgFulfillmentRate: number;
  categoryCount: number;
  surplusCount: number;
  deficitCount: number;
}

function StoreFleetCard({ s }: { s: StoreSummary }) {
  const balanced = s.categoryCount - s.surplusCount - s.deficitCount;
  const borderColor =
    s.avgStockoutRate > 0.3 ? '#f87171'
    : s.avgStockoutRate > 0.1 ? '#fbbf24'
    : '#34d399';

  return (
    <div
      className="bg-white rounded-2xl border border-gray-100 shadow-card hover:shadow-card-hover
                 hover:border-indigo-200 transition-all duration-200 border-l-4 p-4 group cursor-pointer"
      style={{ borderLeftColor: borderColor }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
          <Store className="h-4 w-4 text-indigo-500" />
        </div>
        <span className="text-xs bg-gray-50 text-gray-400 px-2 py-0.5 rounded-full">
          {s.categoryCount} cat.
        </span>
      </div>
      <p className="text-sm font-bold text-gray-800 group-hover:text-indigo-700 transition-colors">
        {s.storeId}
      </p>
      <p className="text-xs text-gray-400 mb-2">{s.region}</p>

      {/* Health bar */}
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden flex mb-1.5">
        <div className="h-full bg-emerald-400 transition-all"
          style={{ width: `${(s.surplusCount / s.categoryCount) * 100}%` }} />
        <div className="h-full bg-gray-200 transition-all"
          style={{ width: `${(balanced / s.categoryCount) * 100}%` }} />
        <div className="h-full bg-rose-400 transition-all"
          style={{ width: `${(s.deficitCount / s.categoryCount) * 100}%` }} />
      </div>

      <p className="text-xs font-semibold text-gray-700">{fmtCurrency(s.totalRevenue)}</p>
      <div className="flex items-center gap-1 mt-1.5">
        <ChevronRight className="h-3 w-3 text-gray-300 group-hover:text-indigo-400 transition-colors" />
        <span className="text-xs text-gray-300 group-hover:text-indigo-400 transition-colors">
          View detail
        </span>
      </div>
    </div>
  );
}

// ── Custom scatter tooltip ────────────────────────────────────────────────────

const ScatterTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="bg-white rounded-xl border border-gray-200 px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-gray-800 mb-1">{d.name}</p>
      <p className="text-emerald-600">Revenue: {fmtCurrency(d.revenue)}</p>
      <p className="text-rose-500">Lost Sales: {fmtCurrency(d.lostSales)}</p>
    </div>
  );
};

// ── Main Page ─────────────────────────────────────────────────────────────────

type SortKey = 'risk' | 'revenue' | 'region';

export default function FleetDashboard() {
  const [cache, setCache] = useState<EnterpriseCache | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('revenue');

  useEffect(() => {
    setCache(loadEnterpriseCache());
  }, []);

  // Reload when user returns to this tab
  useEffect(() => {
    const onFocus = () => setCache(loadEnterpriseCache());
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  // ── Derived data ────────────────────────────────────────────────────────────

  const storeSummaries = useMemo<StoreSummary[]>(() => {
    if (!cache) return [];
    const groups: Record<string, StoreCategoryStat[]> = {};
    for (const s of cache.stores) {
      if (!groups[s.store_id]) groups[s.store_id] = [];
      groups[s.store_id].push(s);
    }
    return Object.entries(groups).map(([storeId, rows]) => ({
      storeId,
      region: rows[0].region,
      totalRevenue: rows.reduce((a, r) => a + r.total_revenue, 0),
      avgStockoutRate: rows.reduce((a, r) => a + r.stockout_rate, 0) / rows.length,
      avgFulfillmentRate: rows.reduce((a, r) => a + r.fulfillment_rate, 0) / rows.length,
      categoryCount: rows.length,
      surplusCount: rows.filter(r => r.avg_stock_level > r.avg_demand).length,
      deficitCount: rows.filter(r => r.avg_stock_level < r.avg_demand).length,
    }));
  }, [cache]);

  const sortedStores = useMemo(() => {
    return [...storeSummaries].sort((a, b) =>
      sortKey === 'risk' ? b.avgStockoutRate - a.avgStockoutRate
      : sortKey === 'revenue' ? b.totalRevenue - a.totalRevenue
      : a.region.localeCompare(b.region)
    );
  }, [storeSummaries, sortKey]);

  const categoryChartData = useMemo(() =>
    (cache?.categories ?? []).map(c => ({
      name: c.product_category,
      Stockout: +(c.stockout_rate * 100).toFixed(1),
      Overstock: +(c.overstock_rate * 100).toFixed(1),
      Fulfillment: +(c.fulfillment_rate * 100).toFixed(1),
    })),
    [cache]
  );

  const regionChartData = useMemo(() =>
    [...(cache?.regions ?? [])]
      .sort((a, b) => b.total_revenue - a.total_revenue)
      .map(r => ({
        region: r.region,
        Revenue: r.total_revenue,
        'Holding Cost': r.total_holding_cost,
        'Lost Sales': r.lost_sales_value,
      })),
    [cache]
  );

  const scatterData = useMemo(() =>
    (cache?.categories ?? []).map(c => ({
      name: c.product_category,
      revenue: c.total_revenue,
      lostSales: c.lost_sales_value,
    })),
    [cache]
  );

  // ── Empty state ─────────────────────────────────────────────────────────────

  if (!cache) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Fleet Dashboard</h2>
          <p className="mt-0.5 text-sm text-gray-500">Enterprise-wide inventory health across all stores</p>
        </div>
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-20 text-center">
          <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Building2 className="h-8 w-8 text-indigo-300" />
          </div>
          <h3 className="text-base font-semibold text-gray-600 mb-1">No enterprise data loaded</h3>
          <p className="text-sm text-gray-400 max-w-xs mx-auto mb-6">
            Upload an enterprise CSV from the Stock Transfer or Simulate pages to populate this dashboard.
          </p>
          <Link
            to="/transfers"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm"
            style={{ background: 'linear-gradient(135deg, #4f46e5, #6366f1)' }}
          >
            <Upload className="h-4 w-4" />
            Upload via Stock Transfer
          </Link>
        </div>
      </div>
    );
  }

  const agg = cache.aggregate;

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Fleet Dashboard</h2>
          <p className="mt-0.5 text-sm text-gray-500">
            Enterprise-wide inventory health across all stores
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100">
            <Database className="h-3.5 w-3.5" />
            {cache.fileName}
            {agg.date_range && (
              <span className="text-indigo-400">
                · {agg.date_range.start} → {agg.date_range.end}
              </span>
            )}
          </span>
          <button
            onClick={() => setCache(loadEnterpriseCache())}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-500 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-all shadow-card"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Reload
          </button>
        </div>
      </div>

      {/* ── KPI strip (8 cards, 4-col) ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard icon={DollarSign} iconBg="bg-emerald-50" iconColor="text-emerald-500"
          label="Total Revenue" value={fmtCurrency(agg.total_revenue)}
          badge={agg.date_range ? `${agg.date_range.days}d` : 'All time'}
          badgeColor="bg-emerald-50 text-emerald-600" />
        <KpiCard icon={CheckCircle2} iconBg="bg-indigo-50" iconColor="text-indigo-500"
          label="Fulfillment Rate" value={fmtPct(agg.fulfillment_rate)}
          badge="Fleet avg" badgeColor="bg-indigo-50 text-indigo-600" />
        <KpiCard icon={AlertCircle} iconBg="bg-red-50" iconColor="text-red-500"
          label="Stockout Rate" value={fmtPct(agg.stockout_rate)}
          badge="Risk" badgeColor="bg-red-50 text-red-500" />
        <KpiCard icon={Package} iconBg="bg-amber-50" iconColor="text-amber-500"
          label="Overstock Rate" value={fmtPct(agg.overstock_rate)}
          badge="Risk" badgeColor="bg-amber-50 text-amber-600" />
        <KpiCard icon={TrendingDown} iconBg="bg-rose-50" iconColor="text-rose-500"
          label="Lost Sales Value" value={fmtCurrency(agg.total_lost_sales_value)}
          badge="Revenue at risk" badgeColor="bg-rose-50 text-rose-500" />
        <KpiCard icon={Database} iconBg="bg-violet-50" iconColor="text-violet-500"
          label="Holding Cost" value={fmtCurrency(agg.total_holding_cost)}
          badge="Fleet total" badgeColor="bg-violet-50 text-violet-600" />
        <KpiCard icon={Store} iconBg="bg-sky-50" iconColor="text-sky-500"
          label="Stores" value={agg.unique_stores}
          badge={`${agg.unique_regions} regions`} badgeColor="bg-sky-50 text-sky-600" />
        <KpiCard icon={Star} iconBg="bg-teal-50" iconColor="text-teal-500"
          label="Avg Seller Quality" value={fmtPct(agg.avg_seller_quality)}
          badge="Quality index" badgeColor="bg-teal-50 text-teal-600" />
      </div>

      {/* ── Charts row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category risk breakdown */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Category Risk Breakdown</h3>
            <p className="text-xs text-gray-400 mt-0.5">Stockout, overstock and fulfillment rates by category</p>
          </div>
          {categoryChartData.length === 0 ? (
            <p className="text-sm text-gray-400 py-10 text-center">No category data</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categoryChartData} margin={{ top: 5, right: 10, left: -20, bottom: 55 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }}
                  angle={-35} textAnchor="end" interval={0} />
                <YAxis unit="%" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => v + '%'} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '12px' }} />
                <Bar dataKey="Stockout" fill="#ef4444" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Overstock" fill="#f59e0b" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Fulfillment" fill="#6366f1" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Revenue vs Lost Sales scatter */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Revenue vs Lost Sales by Category</h3>
            <p className="text-xs text-gray-400 mt-0.5">Each point is a product category — top-left = high risk</p>
          </div>
          {scatterData.length === 0 ? (
            <p className="text-sm text-gray-400 py-10 text-center">No data</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" dataKey="revenue" name="Revenue"
                  tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                  tickFormatter={v => `₹${(v / 100000).toFixed(0)}L`}
                  label={{ value: 'Revenue →', position: 'insideBottom', offset: -12, fontSize: 10, fill: '#94a3b8' }} />
                <YAxis type="number" dataKey="lostSales" name="Lost Sales"
                  tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                  tickFormatter={v => `₹${(v / 100000).toFixed(0)}L`}
                  label={{ value: 'Lost Sales ↑', angle: -90, position: 'insideLeft', offset: 15, fontSize: 10, fill: '#94a3b8' }} />
                <ZAxis range={[60, 60]} />
                <Tooltip content={<ScatterTooltip />} />
                <Scatter data={scatterData} fill="#6366f1" fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Region revenue horizontal bar */}
      {regionChartData.length > 0 && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700">Revenue, Holding Cost &amp; Lost Sales by Region</h3>
            <p className="text-xs text-gray-400 mt-0.5">Sorted by total revenue descending</p>
          </div>
          <ResponsiveContainer width="100%" height={Math.max(180, regionChartData.length * 52)}>
            <BarChart layout="vertical" data={regionChartData} margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                tickFormatter={v => `₹${(v / 100000).toFixed(0)}L`} />
              <YAxis type="category" dataKey="region" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => fmtCurrency(v)} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="Revenue" fill="#6366f1" radius={[0, 3, 3, 0]} />
              <Bar dataKey="Holding Cost" fill="#f59e0b" radius={[0, 3, 3, 0]} />
              <Bar dataKey="Lost Sales" fill="#ef4444" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Store health grid (drill-through) ── */}
      <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Store className="h-4 w-4 text-indigo-400" />
              Store Health — Click to drill through
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {storeSummaries.length} stores · left border = risk level
              <span className="ml-2 inline-flex gap-1.5">
                <span className="text-emerald-500">■</span> low
                <span className="text-amber-500">■</span> medium
                <span className="text-red-400">■</span> high
              </span>
            </p>
          </div>
          {/* Sort controls */}
          <div className="flex items-center gap-1.5">
            <ArrowUpDown className="h-3.5 w-3.5 text-gray-400" />
            {(['revenue', 'risk', 'region'] as SortKey[]).map(k => (
              <button key={k}
                onClick={() => setSortKey(k)}
                className={`text-xs px-3 py-1 rounded-full transition-all font-medium capitalize ${
                  sortKey === k
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }`}
              >
                {k}
              </button>
            ))}
          </div>
        </div>

        {sortedStores.length === 0 ? (
          <p className="text-sm text-gray-400 py-8 text-center">No store data available</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {sortedStores.map(s => (
              <Link key={s.storeId} to={`/store/${encodeURIComponent(s.storeId)}`}>
                <StoreFleetCard s={s} />
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* ── Category detail table ── */}
      {cache.categories.length > 0 && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-700">Category Performance Table</h3>
              <p className="text-xs text-gray-400 mt-0.5">{cache.categories.length} categories</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-100">
                  {['Category', 'Avg Price', 'Avg Stock', 'Avg Demand', 'Fulfillment', 'Stockout', 'Overstock', 'Revenue', 'Lost Sales'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {cache.categories.map((c, i) => {
                  const stockoutBadge =
                    c.stockout_rate > 0.3 ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
                    : c.stockout_rate > 0.1 ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
                    : 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200';
                  const overstockBadge =
                    c.overstock_rate > 0.5 ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
                    : c.overstock_rate > 0.2 ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
                    : 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200';
                  return (
                    <tr key={c.product_category} className={i % 2 === 0 ? '' : 'bg-gray-50/30'}>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-800 whitespace-nowrap">
                        {c.product_category}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{fmtCurrency(c.avg_price)}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{fmt(c.avg_stock_level)}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{fmt(c.avg_demand)}</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${c.fulfillment_rate * 100}%` }} />
                          </div>
                          <span className="text-xs text-gray-600">{fmtPct(c.fulfillment_rate)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${stockoutBadge}`}>
                          {fmtPct(c.stockout_rate)}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${overstockBadge}`}>
                          {fmtPct(c.overstock_rate)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-700 whitespace-nowrap">
                        {fmtCurrency(c.total_revenue)}
                      </td>
                      <td className="px-4 py-3 text-sm text-rose-500 font-medium whitespace-nowrap">
                        {fmtCurrency(c.lost_sales_value)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
