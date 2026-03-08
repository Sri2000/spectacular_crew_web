import { useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, ComposedChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  ArrowLeft, Store, MapPin, TrendingUp, AlertTriangle,
  Package, DollarSign, Building2,
} from 'lucide-react';
import { loadEnterpriseCache } from '../utils/enterpriseCache';
import { StoreCategoryStat } from '../services/api';

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('en-IN', { maximumFractionDigits: decimals });
}
function pct(n: number) {
  return (n * 100).toFixed(1) + '%';
}
function currency(n: number) {
  if (n >= 1_000_000) return '₹' + (n / 1_000_000).toFixed(2) + 'M';
  if (n >= 1_000) return '₹' + (n / 1_000).toFixed(1) + 'K';
  return '₹' + n.toFixed(0);
}

// ── Sub-components ─────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  trend?: 'good' | 'bad' | 'neutral';
}

function KpiCard({ label, value, sub, icon: Icon, iconBg, iconColor, trend }: KpiCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex items-start space-x-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${iconBg}`}>
        <Icon className={`h-5 w-5 ${iconColor}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gray-900 mt-0.5 leading-tight">{value}</p>
        {sub && (
          <p className={`text-xs mt-0.5 ${
            trend === 'good' ? 'text-emerald-600' :
            trend === 'bad'  ? 'text-red-500' :
            'text-gray-400'
          }`}>{sub}</p>
        )}
      </div>
    </div>
  );
}

// Risk badge
function RiskBadge({ rate, label }: { rate: number; label: string }) {
  const pctVal = rate * 100;
  const color =
    pctVal >= 40 ? 'bg-red-100 text-red-700 border-red-200' :
    pctVal >= 20 ? 'bg-amber-100 text-amber-700 border-amber-200' :
                  'bg-emerald-100 text-emerald-700 border-emerald-200';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
      {label}: {pct(rate)}
    </span>
  );
}

// Fulfillment progress bar
function FulfillmentBar({ rate }: { rate: number }) {
  const pctVal = Math.min(100, rate * 100);
  const color = pctVal >= 90 ? 'bg-emerald-500' : pctVal >= 70 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center space-x-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pctVal}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-600 w-12 text-right">{pct(rate)}</span>
    </div>
  );
}

// ── Tooltip styles ─────────────────────────────────────────────────────────────

const tooltipStyle = {
  contentStyle: {
    borderRadius: '12px',
    border: '1px solid #e2e8f0',
    fontSize: '12px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
  },
};

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function StoreDashboard() {
  const { storeId } = useParams<{ storeId: string }>();
  const navigate = useNavigate();
  const cache = loadEnterpriseCache();

  // Redirect if no cache
  useEffect(() => {
    if (!cache) navigate('/dashboard');
  }, [cache, navigate]);

  // Filter rows for this store
  const storeRows: StoreCategoryStat[] = useMemo(() => {
    if (!cache || !storeId) return [];
    return cache.stores.filter(s => s.store_id === storeId);
  }, [cache, storeId]);

  // Aggregate KPIs across categories for this store
  const kpis = useMemo(() => {
    if (!storeRows.length) return null;
    const totalRevenue = storeRows.reduce((s, r) => s + r.total_revenue, 0);
    const avgFulfillment = storeRows.reduce((s, r) => s + r.fulfillment_rate, 0) / storeRows.length;
    const avgStockout = storeRows.reduce((s, r) => s + r.stockout_rate, 0) / storeRows.length;
    const avgLostUnits = storeRows.reduce((s, r) => s + r.avg_lost_sales_units, 0) / storeRows.length;
    const totalHolding = storeRows.reduce((s, r) => s + (r.avg_holding_cost * r.avg_stock_level), 0);
    const region = storeRows[0]?.region ?? '—';
    return { totalRevenue, avgFulfillment, avgStockout, avgLostUnits, totalHolding, region };
  }, [storeRows]);

  // Radar data: per-category fulfillment, stockout safety (1 - stockout), overstock safety
  const radarData = useMemo(() =>
    storeRows.map(r => ({
      category: r.product_category,
      Fulfillment: Math.round(r.fulfillment_rate * 100),
      'Stockout Safety': Math.round((1 - r.stockout_rate) * 100),
      'Overstock Safety': Math.round((1 - r.overstock_rate) * 100),
    })),
    [storeRows]
  );

  // Stock vs Demand bar data
  const stockDemandData = useMemo(() =>
    storeRows.map(r => ({
      category: r.product_category,
      'Avg Stock': Math.round(r.avg_stock_level),
      'Avg Demand': Math.round(r.avg_demand),
    })),
    [storeRows]
  );

  // Holding Cost + Lost Units composed chart
  const holdingLostData = useMemo(() =>
    storeRows.map(r => ({
      category: r.product_category,
      'Holding Cost': Math.round(r.avg_holding_cost * r.avg_stock_level * 100) / 100,
      'Lost Units': Math.round(r.avg_lost_sales_units * 100) / 100,
    })),
    [storeRows]
  );

  // Guard: no cache
  if (!cache) return null;

  // Guard: store not found
  if (!storeRows.length) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center">
          <Store className="h-8 w-8 text-gray-400" />
        </div>
        <p className="text-xl font-semibold text-gray-700">Store not found</p>
        <p className="text-sm text-gray-400">No data found for store <span className="font-mono font-semibold">{storeId}</span></p>
        <Link
          to="/dashboard"
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Fleet Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/dashboard"
            className="flex items-center space-x-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Fleet Dashboard</span>
          </Link>
          <span className="text-gray-300">/</span>
          <div>
            <div className="flex items-center space-x-2">
              <div className="w-9 h-9 bg-indigo-100 rounded-xl flex items-center justify-center">
                <Store className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight">
                  Store {storeId}
                </h1>
                {kpis && (
                  <div className="flex items-center space-x-1 mt-0.5">
                    <MapPin className="h-3.5 w-3.5 text-gray-400" />
                    <span className="text-sm text-gray-500">{kpis.region}</span>
                    <span className="text-gray-300 mx-1">·</span>
                    <span className="text-sm text-gray-500">{storeRows.length} categories</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Dataset badge */}
        <div className="text-right">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Dataset</p>
          <p className="text-sm text-gray-600 font-mono mt-0.5">{cache.fileName}</p>
        </div>
      </div>

      {/* ── KPI Cards ───────────────────────────────────────────────────────── */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Total Revenue"
            value={currency(kpis.totalRevenue)}
            icon={DollarSign}
            iconBg="bg-emerald-50"
            iconColor="text-emerald-600"
          />
          <KpiCard
            label="Avg Fulfillment"
            value={pct(kpis.avgFulfillment)}
            sub={kpis.avgFulfillment >= 0.9 ? '↑ Strong performance' : kpis.avgFulfillment >= 0.7 ? 'Moderate' : '↓ Needs attention'}
            trend={kpis.avgFulfillment >= 0.9 ? 'good' : kpis.avgFulfillment >= 0.7 ? 'neutral' : 'bad'}
            icon={TrendingUp}
            iconBg="bg-blue-50"
            iconColor="text-blue-600"
          />
          <KpiCard
            label="Avg Stockout Rate"
            value={pct(kpis.avgStockout)}
            sub={kpis.avgStockout <= 0.1 ? 'Healthy stock levels' : kpis.avgStockout <= 0.25 ? 'Watch closely' : '↑ High stockout risk'}
            trend={kpis.avgStockout <= 0.1 ? 'good' : kpis.avgStockout <= 0.25 ? 'neutral' : 'bad'}
            icon={AlertTriangle}
            iconBg="bg-amber-50"
            iconColor="text-amber-600"
          />
          <KpiCard
            label="Avg Lost Sales/Day"
            value={fmt(kpis.avgLostUnits, 1) + ' units'}
            sub="per category per day"
            icon={Package}
            iconBg="bg-rose-50"
            iconColor="text-rose-600"
            trend={kpis.avgLostUnits <= 1 ? 'good' : kpis.avgLostUnits <= 5 ? 'neutral' : 'bad'}
          />
        </div>
      )}

      {/* ── Charts Row 1 ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Radar: Category Performance */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-1">Category Performance Radar</h2>
          <p className="text-xs text-gray-400 mb-4">Fulfillment, stockout safety & overstock safety per category</p>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData} margin={{ top: 8, right: 24, bottom: 8, left: 24 }}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: '#64748b' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <Radar name="Fulfillment" dataKey="Fulfillment" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
              <Radar name="Stockout Safety" dataKey="Stockout Safety" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
              <Radar name="Overstock Safety" dataKey="Overstock Safety" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }} />
              <Tooltip {...tooltipStyle} formatter={(v: number) => [v + '%']} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* BarChart: Stock vs Demand */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-1">Stock vs Demand by Category</h2>
          <p className="text-xs text-gray-400 mb-4">Average daily stock level compared to average demand</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stockDemandData} margin={{ top: 8, right: 16, bottom: 32, left: 8 }}
              barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="category" tick={{ fontSize: 10, fill: '#94a3b8' }}
                angle={-30} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip {...tooltipStyle} />
              <Legend iconType="square" iconSize={8} wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <Bar dataKey="Avg Stock" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Avg Demand" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Chart Row 2: Holding Cost + Lost Units ───────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <h2 className="text-base font-semibold text-gray-800 mb-1">Holding Cost vs Lost Sales Units</h2>
        <p className="text-xs text-gray-400 mb-4">Daily holding cost (bars) and average lost sales units (line) — dual axis</p>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart data={holdingLostData} margin={{ top: 8, right: 40, bottom: 32, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="category" tick={{ fontSize: 10, fill: '#94a3b8' }}
              angle={-30} textAnchor="end" interval={0} />
            <YAxis yAxisId="left" tick={{ fontSize: 11, fill: '#94a3b8' }}
              label={{ value: 'Holding Cost (₹)', angle: -90, position: 'insideLeft', offset: 12, style: { fontSize: '10px', fill: '#94a3b8' } }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11, fill: '#94a3b8' }}
              label={{ value: 'Lost Units', angle: 90, position: 'insideRight', offset: 12, style: { fontSize: '10px', fill: '#94a3b8' } }} />
            <Tooltip {...tooltipStyle} />
            <Legend iconSize={8} wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
            <Bar yAxisId="left" dataKey="Holding Cost" fill="#a78bfa" radius={[4, 4, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="Lost Units" stroke="#f43f5e"
              strokeWidth={2.5} dot={{ r: 4, fill: '#f43f5e' }} activeDot={{ r: 6 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ── Category Detail Table ────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-800">Category Detail</h2>
          <p className="text-xs text-gray-400 mt-0.5">All inventory metrics broken down by product category</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Avg Stock</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Avg Demand</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Revenue</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Fulfillment</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">Risk Flags</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">Avg Price</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {storeRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50/60 transition-colors">
                  <td className="px-4 py-3.5">
                    <span className="font-semibold text-gray-800">{row.product_category}</span>
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-gray-600">{fmt(row.avg_stock_level, 1)}</td>
                  <td className="px-4 py-3.5 text-right font-mono text-gray-600">{fmt(row.avg_demand, 1)}</td>
                  <td className="px-4 py-3.5 text-right font-mono text-gray-700 font-medium">{currency(row.total_revenue)}</td>
                  <td className="px-4 py-3.5 w-40">
                    <FulfillmentBar rate={row.fulfillment_rate} />
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex flex-wrap gap-1 justify-center">
                      {row.stockout_rate > 0.05 && <RiskBadge rate={row.stockout_rate} label="OUT" />}
                      {row.overstock_rate > 0.05 && <RiskBadge rate={row.overstock_rate} label="OVER" />}
                      {row.stockout_rate <= 0.05 && row.overstock_rate <= 0.05 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Healthy
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-right font-mono text-gray-600">₹{fmt(row.avg_price, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Back Link Footer ─────────────────────────────────────────────────── */}
      <div className="flex justify-center pb-4">
        <Link
          to="/dashboard"
          className="flex items-center space-x-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium transition-colors"
        >
          <Building2 className="h-4 w-4" />
          <span>Back to Fleet Dashboard</span>
        </Link>
      </div>

    </div>
  );
}
