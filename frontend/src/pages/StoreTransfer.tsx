import { useState, useCallback } from 'react';
import {
  ArrowLeftRight,
  Upload,
  TrendingDown,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Package,
  DollarSign,
  Store,
  ChevronRight,
  Filter,
  Info,
  Truck,
  Calendar,
  FileSpreadsheet,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import {
  uploadCSV,
  recommendTransfers,
  StoreCategoryStat,
  TransferRecommendation,
  TransferResult,
} from '../services/api';
import { saveEnterpriseCache, loadEnterpriseCache } from '../utils/enterpriseCache';

// ── Formatters ────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n);

const fmtCurrency = (n: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(n);

// ── Strength config ───────────────────────────────────────────────────────────

const STRENGTH_META: Record<
  string,
  {
    label: string;
    textColor: string;
    bgColor: string;
    ringColor: string;
    borderLeft: string;
    icon: typeof CheckCircle2;
  }
> = {
  Strong: {
    label: 'Strong',
    textColor: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
    ringColor: 'ring-emerald-200',
    borderLeft: 'border-l-emerald-500',
    icon: CheckCircle2,
  },
  Moderate: {
    label: 'Moderate',
    textColor: 'text-blue-700',
    bgColor: 'bg-blue-50',
    ringColor: 'ring-blue-200',
    borderLeft: 'border-l-blue-400',
    icon: TrendingUp,
  },
  Marginal: {
    label: 'Marginal',
    textColor: 'text-amber-700',
    bgColor: 'bg-amber-50',
    ringColor: 'ring-amber-200',
    borderLeft: 'border-l-amber-400',
    icon: AlertCircle,
  },
  'Not Viable': {
    label: 'Not Viable',
    textColor: 'text-gray-500',
    bgColor: 'bg-gray-100',
    ringColor: 'ring-gray-200',
    borderLeft: 'border-l-gray-300',
    icon: TrendingDown,
  },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function KpiCard({
  icon: Icon,
  iconBg,
  iconColor,
  label,
  value,
  badge,
  badgeColor,
}: {
  icon: typeof Store;
  iconBg: string;
  iconColor: string;
  label: string;
  value: string | number;
  badge?: string;
  badgeColor?: string;
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
      <p className="text-3xl font-bold text-gray-900 mt-4">{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function StoreHealthCard({
  storeId,
  stats,
}: {
  storeId: string;
  stats: StoreCategoryStat[];
}) {
  const region = stats[0]?.region ?? '—';
  const surplus = stats.filter(s => s.avg_stock_level > s.avg_demand).length;
  const deficit = stats.filter(s => s.avg_stock_level < s.avg_demand).length;
  const balanced = stats.length - surplus - deficit;
  const total = stats.length;

  const surplusPct = total ? (surplus / total) * 100 : 0;
  const deficitPct = total ? (deficit / total) * 100 : 0;
  const balancedPct = total ? (balanced / total) * 100 : 0;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 hover:shadow-card-hover transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
            <Store className="h-4 w-4 text-indigo-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{storeId}</p>
            <p className="text-xs text-gray-400">{region}</p>
          </div>
        </div>
        <span className="text-xs bg-gray-50 text-gray-400 px-2 py-0.5 rounded-full">
          {total} cat.
        </span>
      </div>

      {/* Stacked health bar */}
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden flex mb-2">
        {surplusPct > 0 && (
          <div className="h-full bg-emerald-400 transition-all" style={{ width: `${surplusPct}%` }} />
        )}
        {balancedPct > 0 && (
          <div className="h-full bg-gray-200 transition-all" style={{ width: `${balancedPct}%` }} />
        )}
        {deficitPct > 0 && (
          <div className="h-full bg-rose-400 transition-all" style={{ width: `${deficitPct}%` }} />
        )}
      </div>

      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        {surplus > 0 && (
          <span className="flex items-center gap-1 text-xs text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            {surplus} surplus
          </span>
        )}
        {deficit > 0 && (
          <span className="flex items-center gap-1 text-xs text-rose-500">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
            {deficit} deficit
          </span>
        )}
        {balanced > 0 && (
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-300 inline-block" />
            {balanced} balanced
          </span>
        )}
      </div>
    </div>
  );
}

function TransferCard({ t }: { t: TransferRecommendation }) {
  const meta = STRENGTH_META[t.recommendation_strength] ?? STRENGTH_META['Not Viable'];
  const StrengthIcon = meta.icon;

  return (
    <div
      className={`bg-white rounded-2xl border border-gray-100 shadow-card hover:shadow-card-hover transition-all duration-200 border-l-4 overflow-hidden`}
      style={{
        borderLeftColor:
          t.recommendation_strength === 'Strong'
            ? '#10b981'
            : t.recommendation_strength === 'Moderate'
            ? '#60a5fa'
            : t.recommendation_strength === 'Marginal'
            ? '#fbbf24'
            : '#d1d5db',
      }}
    >
      {/* Card header */}
      <div className="px-5 py-4 flex items-center justify-between border-b border-gray-50">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-gray-300 font-bold">#{t.priority_rank}</span>
          <span
            className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ring-1 ${meta.bgColor} ${meta.textColor} ${meta.ringColor}`}
          >
            <StrengthIcon className="h-3 w-3" />
            {meta.label}
          </span>
          <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100">
            <Package className="h-3 w-3" />
            {t.product_category}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Truck className="h-3.5 w-3.5" />
          <span className="font-medium">{fmt(t.transfer_quantity)} units to move</span>
        </div>
      </div>

      {/* Source → Destination flow */}
      <div className="px-5 py-4 flex items-stretch gap-3">
        {/* Source */}
        <div className="flex-1 rounded-xl bg-emerald-50 border border-emerald-100 p-3.5">
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            Source · Surplus
          </p>
          <p className="text-base font-bold text-gray-800">{t.source_store.store_id}</p>
          <p className="text-xs text-gray-500 mb-2">{t.source_store.region}</p>
          <div className="flex flex-col gap-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Stock</span>
              <span className="font-medium text-gray-700">{fmt(t.source_store.avg_stock_level)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Demand</span>
              <span className="font-medium text-gray-700">{fmt(t.source_store.avg_demand)}</span>
            </div>
            <div className="flex justify-between border-t border-emerald-100 pt-1 mt-0.5">
              <span className="text-emerald-600 font-semibold">Excess Units</span>
              <span className="font-bold text-emerald-700">+{fmt(t.source_store.excess_units ?? 0)}</span>
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div className="flex flex-col items-center justify-center gap-1.5 flex-shrink-0 px-1">
          <div className="w-8 h-8 bg-indigo-50 rounded-full flex items-center justify-center">
            <ArrowRight className="h-4 w-4 text-indigo-500" />
          </div>
          <span className="text-xs text-gray-400 font-medium">{fmt(t.transfer_quantity)}u</span>
        </div>

        {/* Destination */}
        <div className="flex-1 rounded-xl bg-rose-50 border border-rose-100 p-3.5">
          <p className="text-xs font-semibold text-rose-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
            Destination · Deficit
          </p>
          <p className="text-base font-bold text-gray-800">{t.destination_store.store_id}</p>
          <p className="text-xs text-gray-500 mb-2">{t.destination_store.region}</p>
          <div className="flex flex-col gap-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Stock</span>
              <span className="font-medium text-gray-700">{fmt(t.destination_store.avg_stock_level)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Demand</span>
              <span className="font-medium text-gray-700">{fmt(t.destination_store.avg_demand)}</span>
            </div>
            <div className="flex justify-between border-t border-rose-100 pt-1 mt-0.5">
              <span className="text-rose-500 font-semibold">Demand Gap</span>
              <span className="font-bold text-rose-600">-{fmt(t.destination_store.deficit_units ?? 0)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Economics footer */}
      <div className="px-5 pb-4">
        <div className="rounded-xl bg-gray-50 border border-gray-100 grid grid-cols-4 divide-x divide-gray-100 overflow-hidden">
          <div className="px-4 py-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Holding Saved</p>
            <p className="text-sm font-bold text-emerald-600">{fmtCurrency(t.economics.saved_holding_cost)}</p>
          </div>
          <div className="px-4 py-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Procurement Saved</p>
            <p className="text-sm font-bold text-emerald-600">{fmtCurrency(t.economics.saved_procurement_cost)}</p>
          </div>
          <div className="px-4 py-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Transport Cost</p>
            <p className="text-sm font-bold text-rose-500">{fmtCurrency(t.economics.transport_cost)}</p>
          </div>
          <div className="px-4 py-3 text-center">
            <p className="text-xs text-gray-400 mb-1">Net Benefit</p>
            <p
              className={`text-sm font-extrabold ${
                t.economics.net_benefit >= 0 ? 'text-emerald-700' : 'text-rose-600'
              }`}
            >
              {t.economics.net_benefit >= 0 ? '+' : ''}
              {fmtCurrency(t.economics.net_benefit)}
            </p>
          </div>
        </div>
        {t.is_viable && (
          <p className="text-right text-xs text-gray-400 mt-2">
            ROI on transport spend:{' '}
            <span className="font-semibold text-indigo-600">{t.economics.roi_percent}%</span>
          </p>
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function StoreTransfer() {
  const cachedData = loadEnterpriseCache();
  const cachedStores = cachedData?.stores && cachedData.stores.length > 0 ? cachedData.stores : null;

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [transportCost, setTransportCost] = useState<string>('5');
  const [horizonDays, setHorizonDays] = useState<string>('30');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storeStats, setStoreStats] = useState<StoreCategoryStat[] | null>(cachedStores);
  const [result, setResult] = useState<TransferResult | null>(null);
  const [filter, setFilter] = useState<'viable' | 'all'>('viable');

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const runTransferAnalysis = async (ss: StoreCategoryStat[]) => {
    const cost = parseFloat(transportCost) || 0;
    const days = parseInt(horizonDays) || 30;
    const rec = await recommendTransfers(ss, cost, days);
    setResult(rec);
  };

  const handleAnalyzeFromCache = async () => {
    if (!cachedStores) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setStoreStats(cachedStores);
      await runTransferAnalysis(cachedStores);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const ingestion = await uploadCSV('enterprise', file);
      if (!ingestion.success) {
        setError(ingestion.errors?.join(', ') ?? 'Upload failed');
        return;
      }
      const ss: StoreCategoryStat[] = ingestion.store_stats ?? [];
      if (ss.length === 0) {
        setError('No store-level data found. Ensure the file has store_id and product_category columns.');
        return;
      }
      setStoreStats(ss);
      saveEnterpriseCache({
        savedAt: new Date().toISOString(),
        fileName: file.name,
        recordsCount: ingestion.records_count,
        aggregate: ingestion.aggregate_stats,
        categories: ingestion.category_stats ?? [],
        regions: ingestion.region_stats ?? [],
        stores: ss,
      });
      await runTransferAnalysis(ss);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Group stats by store for the overview grid
  const storeGroups: Record<string, StoreCategoryStat[]> = {};
  if (storeStats) {
    for (const s of storeStats) {
      if (!storeGroups[s.store_id]) storeGroups[s.store_id] = [];
      storeGroups[s.store_id].push(s);
    }
  }

  const displayedTransfers =
    result?.transfers.filter(t => filter === 'all' || t.is_viable) ?? [];

  return (
    <div className="space-y-6">
      {/* ── Page header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Stock Transfer Optimizer</h2>
          <p className="mt-0.5 text-sm text-gray-500">
            Rebalance inventory across stores — avoid procurement, cut holding costs
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 ring-1 ring-indigo-100">
          <Sparkles className="h-3.5 w-3.5" />
          Optimization Engine
        </span>
      </div>

      {/* ── How it works strip ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-card px-6 py-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5" /> How it works
        </p>
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              step: '1',
              title: 'Identify imbalances',
              desc: 'Finds stores with excess stock and stores running low on the same product category.',
              color: 'bg-indigo-50 text-indigo-600',
            },
            {
              step: '2',
              title: 'Calculate economics',
              desc: 'Compares savings (holding cost + avoided procurement) against your transport cost.',
              color: 'bg-violet-50 text-violet-600',
            },
            {
              step: '3',
              title: 'Rank by net benefit',
              desc: 'Only recommends moves where you save more than you spend. Sorted by highest ROI.',
              color: 'bg-emerald-50 text-emerald-600',
            },
          ].map(item => (
            <div key={item.step} className="flex items-start gap-3">
              <span
                className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${item.color}`}
              >
                {item.step}
              </span>
              <div>
                <p className="text-sm font-semibold text-gray-700">{item.title}</p>
                <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Cache banner ── */}
      {cachedStores && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-2xl px-5 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-indigo-800">
                Dataset already uploaded — {cachedData!.fileName}
              </p>
              <p className="text-xs text-indigo-500 mt-0.5">
                {cachedStores.length} store×category records · {cachedData!.recordsCount.toLocaleString()} rows
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-indigo-600">Transport cost (₹)</label>
              <input
                type="number" min="0" step="0.5" value={transportCost}
                onChange={e => setTransportCost(e.target.value)}
                className="w-28 px-3 py-1.5 rounded-lg border border-indigo-200 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-indigo-600">Horizon (days)</label>
              <input
                type="number" min="1" max="365" value={horizonDays}
                onChange={e => setHorizonDays(e.target.value)}
                className="w-24 px-3 py-1.5 rounded-lg border border-indigo-200 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
            </div>
            <button
              onClick={handleAnalyzeFromCache}
              disabled={loading}
              className="self-end flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold text-white disabled:opacity-50 transition-all hover:brightness-110"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #6366f1)' }}
            >
              {loading ? (
                <span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Analyse Transfers
            </button>
          </div>
        </div>
      )}

      {/* ── Upload card (only shown when no cached data) ── */}
      {!cachedStores && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <FileSpreadsheet className="h-4 w-4 text-indigo-400" />
            Upload Data &amp; Configure Parameters
          </h3>

          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById('transfer-file-input')?.click()}
            className={`rounded-xl border-2 border-dashed cursor-pointer transition-all mb-5 p-8 text-center ${
              dragging ? 'border-indigo-400 bg-indigo-50/40'
              : file ? 'border-emerald-300 bg-emerald-50/30'
              : 'border-gray-200 bg-gray-50/50 hover:border-indigo-300 hover:bg-indigo-50/20'
            }`}
          >
            {file ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                </div>
                <p className="text-sm font-semibold text-emerald-700">{file.name}</p>
                <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(0)} KB · Click to replace</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                  <Upload className="h-5 w-5 text-gray-400" />
                </div>
                <p className="text-sm font-medium text-gray-600">
                  Drag &amp; drop or <span className="text-indigo-600 underline underline-offset-2">browse</span>
                </p>
                <p className="text-xs text-gray-400">Enterprise CSV or Excel</p>
              </div>
            )}
            <input id="transfer-file-input" type="file" accept=".csv,.xlsx,.xls" className="hidden"
              onChange={e => setFile(e.target.files?.[0] ?? null)} />
          </div>

          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-gray-500 flex items-center gap-1.5">
                <Truck className="h-3.5 w-3.5 text-gray-400" /> Transport cost per unit (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400 font-medium">₹</span>
                <input type="number" min="0" step="0.5" value={transportCost}
                  onChange={e => setTransportCost(e.target.value)}
                  className="pl-7 pr-3 py-2 w-36 rounded-xl border border-gray-200 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all" />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-gray-500 flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-gray-400" /> Planning horizon (days)
              </label>
              <input type="number" min="1" max="365" value={horizonDays}
                onChange={e => setHorizonDays(e.target.value)}
                className="px-3 py-2 w-28 rounded-xl border border-gray-200 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 transition-all" />
            </div>
            <div className="flex-1" />
            <button onClick={handleAnalyze} disabled={!file || loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #6366f1)' }}>
              {loading ? <><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Analysing…</>
                : <><Sparkles className="h-4 w-4" />Analyse Transfers<ChevronRight className="h-4 w-4" /></>}
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl px-4 py-3 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* ── Results ── */}
      {result && (
        <>
          {/* KPI strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard
              icon={ArrowLeftRight}
              iconBg="bg-indigo-50"
              iconColor="text-indigo-500"
              label="Transfer Opportunities"
              value={result.total_opportunities}
              badge="Found"
              badgeColor="bg-gray-50 text-gray-400"
            />
            <KpiCard
              icon={CheckCircle2}
              iconBg="bg-emerald-50"
              iconColor="text-emerald-500"
              label="Viable Transfers"
              value={result.viable_transfers}
              badge="Net positive"
              badgeColor="bg-emerald-50 text-emerald-600"
            />
            <KpiCard
              icon={DollarSign}
              iconBg="bg-violet-50"
              iconColor="text-violet-500"
              label="Total Potential Savings"
              value={fmtCurrency(result.total_potential_savings)}
              badge={`${result.time_horizon_days}d horizon`}
              badgeColor="bg-violet-50 text-violet-600"
            />
            <KpiCard
              icon={Store}
              iconBg="bg-amber-50"
              iconColor="text-amber-500"
              label="Stores Involved"
              value={result.stores_involved}
              badge="Impacted"
              badgeColor="bg-amber-50 text-amber-600"
            />
          </div>

          {/* Store overview grid */}
          {Object.keys(storeGroups).length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Store className="h-4 w-4 text-indigo-400" />
                  Store Health Overview
                </h3>
                <span className="text-xs text-gray-400">
                  {Object.keys(storeGroups).length} stores · {storeStats?.length ?? 0} category records
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {Object.entries(storeGroups).map(([storeId, stats]) => (
                  <StoreHealthCard key={storeId} storeId={storeId} stats={stats} />
                ))}
              </div>
            </div>
          )}

          {/* Transfer recommendations */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <ArrowLeftRight className="h-4 w-4 text-indigo-400" />
                Transfer Recommendations
                <span className="text-xs font-normal text-gray-400">
                  — sorted by net benefit
                </span>
              </h3>
              <div className="flex items-center gap-1.5">
                <Filter className="h-3.5 w-3.5 text-gray-400" />
                {(['viable', 'all'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`text-xs px-3 py-1.5 rounded-full transition-all font-medium ${
                      filter === f
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                    }`}
                  >
                    {f === 'viable' ? 'Viable only' : 'Show all'}
                  </button>
                ))}
              </div>
            </div>

            {displayedTransfers.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-12 text-center">
                <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-3">
                  <AlertCircle className="h-6 w-6 text-gray-300" />
                </div>
                <p className="text-sm font-medium text-gray-500">No viable transfers found</p>
                <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                  {filter === 'viable'
                    ? 'Try lowering the transport cost per unit, or switch to "Show all" to see marginal options.'
                    : 'No transfer opportunities detected in this dataset.'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {displayedTransfers.map(t => (
                  <TransferCard key={t.transfer_id} t={t} />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Empty state ── */}
      {!result && !loading && (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-16 text-center">
          <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ArrowLeftRight className="h-7 w-7 text-indigo-300" />
          </div>
          {cachedStores ? (
            <>
              <p className="text-sm font-semibold text-gray-500">Click "Analyse Transfers" above to get recommendations</p>
              <p className="text-xs text-gray-400 mt-1 max-w-xs mx-auto">
                Set your transport cost and planning horizon, then run the analysis.
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold text-gray-500">Upload an Enterprise dataset to get started</p>
              <p className="text-xs text-gray-400 mt-1 max-w-xs mx-auto">
                Or upload via Data Upload first — this page will detect it automatically next time.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
