import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { loadEnterpriseCache } from '../utils/enterpriseCache';
import { Play, CheckCircle, XCircle, Info } from 'lucide-react';

interface SimResult { success: boolean; scenario_id?: string; simulation?: any; error?: string; }

export default function SimulateDashboard() {
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<SimResult | null>(null);

  const cache = loadEnterpriseCache();
  const cacheCategories = cache?.categories ?? [];

  const defaultProducts = cacheCategories.map(c => c.product_category).join(', ');
  const avgDemand = cacheCategories.length
    ? Math.round(cacheCategories.reduce((s, c) => s + c.avg_demand, 0) / cacheCategories.length)
    : 50;
  const avgStock = cacheCategories.length
    ? Math.round(cacheCategories.reduce((s, c) => s + c.avg_stock_level, 0) / cacheCategories.length)
    : 1000;
  const avgStockout = cacheCategories.length
    ? cacheCategories.reduce((s, c) => s + c.stockout_rate, 0) / cacheCategories.length
    : 0;
  const avgOverstock = cacheCategories.length
    ? cacheCategories.reduce((s, c) => s + c.overstock_rate, 0) / cacheCategories.length
    : 0;
  const defaultScenario = avgStockout >= avgOverstock ? 'STOCKOUT' : 'OVERSTOCK';

  const inputClass = 'w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition-all';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1.5';

  const handleSimulation = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSimulating(true);
    setSimResult(null);
    const form = new FormData(e.currentTarget);
    const scenarioType = form.get('scenario_type') as string;
    const timeHorizon = parseInt(form.get('time_horizon') as string, 10);
    const affectedProducts = (form.get('affected_products') as string)
      .split(',').map(p => p.trim()).filter(Boolean);

    const seed = {
      product_category: affectedProducts[0] ?? 'UNKNOWN',
      dominant_scenario: scenarioType,
      initial_conditions: { base_inventory: parseInt(form.get('base_inventory') as string, 10) },
      simulation_parameters: { demand_rate: parseFloat(form.get('demand_rate') as string) },
    };

    try {
      const res = await api.post('/api/analysis/simulate-seeded', {
        seed,
        scenario_type: scenarioType,
        time_horizon: timeHorizon,
        affected_products: affectedProducts,
      }, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
      setSimResult({ success: true, scenario_id: res.data.scenario_id, simulation: res.data.simulation });
    } catch (err: any) {
      setSimResult({ success: false, error: err.response?.data?.detail ?? err.message });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Simulate</h2>
        <p className="mt-0.5 text-sm text-gray-500">
          Run failure scenario simulations to model inventory risk
        </p>
      </div>

      {/* Cache info banner */}
      {cache ? (
        <div className="flex items-start space-x-3 px-4 py-3 bg-indigo-50 border border-indigo-200 rounded-xl">
          <Info className="h-4 w-4 text-indigo-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-indigo-700">
            Fields pre-filled from <span className="font-semibold">{cache.fileName}</span>
            {' '}({cache.recordsCount.toLocaleString()} records). You can override any value before running.
          </p>
        </div>
      ) : (
        <div className="flex items-start space-x-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl">
          <Info className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-amber-700">
            Upload an Enterprise dataset first to auto-fill simulation parameters from your real data.
          </p>
        </div>
      )}

      {/* Simulation form */}
      <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #eef2ff, #e0e7ff)' }}>
            <Play className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-gray-900">Configure Scenario</h3>
            <p className="text-xs text-gray-400">Define the failure scenario parameters</p>
          </div>
        </div>

        <div className="p-6">
          <form onSubmit={handleSimulation} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className={labelClass}>Scenario Type</label>
                <select name="scenario_type" defaultValue={defaultScenario} className={inputClass} required>
                  <option value="OVERSTOCK">Overstock</option>
                  <option value="STOCKOUT">Stockout</option>
                  <option value="SEASONAL_MISMATCH">Seasonal Mismatch</option>
                </select>
                {cache && (
                  <p className="mt-1 text-xs text-indigo-500">
                    Auto-detected: {defaultScenario === 'STOCKOUT' ? 'stockout' : 'overstock'} risk dominates
                  </p>
                )}
              </div>

              <div>
                <label className={labelClass}>Time Horizon (days)</label>
                <input type="number" name="time_horizon" defaultValue="30" min="1" max="365" className={inputClass} required />
              </div>

              <div className="md:col-span-2">
                <label className={labelClass}>
                  Affected Products <span className="text-gray-400 font-normal">(comma-separated)</span>
                  {cache && <span className="ml-2 text-xs text-indigo-500 font-normal">from uploaded data</span>}
                </label>
                <input
                  type="text" name="affected_products"
                  defaultValue={defaultProducts || undefined}
                  placeholder="Electronics, Apparel, Home"
                  className={inputClass}
                  required
                />
              </div>

              <div>
                <label className={labelClass}>
                  Base Inventory
                  {cache && <span className="ml-2 text-xs text-indigo-500 font-normal">avg from data</span>}
                </label>
                <input type="number" name="base_inventory" defaultValue={avgStock} min="0" className={inputClass} required />
              </div>

              <div>
                <label className={labelClass}>
                  Demand Rate <span className="text-gray-400 font-normal">(units/day)</span>
                  {cache && <span className="ml-2 text-xs text-indigo-500 font-normal">avg from data</span>}
                </label>
                <input type="number" name="demand_rate" defaultValue={avgDemand} min="0" className={inputClass} required />
              </div>

              <div>
                <label className={labelClass}>Overstock Factor</label>
                <input type="number" name="overstock_factor" defaultValue="2.0" step="0.1" min="1" className={inputClass} />
              </div>
            </div>

            <button
              type="submit"
              disabled={simulating}
              className="w-full flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                background: simulating ? '#a5b4fc' : 'linear-gradient(135deg, #4f46e5, #6366f1)',
                boxShadow: simulating ? 'none' : '0 4px 14px rgba(79,70,229,0.35)',
              }}
            >
              <Play className="h-4 w-4" />
              <span>{simulating ? 'Running Simulation...' : 'Run Simulation'}</span>
            </button>
          </form>

          {simResult && (
            <div className={`mt-5 p-4 rounded-xl border ${simResult.success ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
              {simResult.success ? (
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                    <p className="text-sm font-semibold text-emerald-800">Simulation completed successfully!</p>
                  </div>
                  <div className="space-y-1 font-mono text-xs text-emerald-700 pl-7">
                    <p>Scenario ID: {simResult.scenario_id}</p>
                    <p>Execution time: {simResult.simulation?.execution_time_seconds?.toFixed(2)}s</p>
                  </div>
                  <Link
                    to={`/scenario/${simResult.scenario_id}`}
                    className="inline-flex items-center space-x-1.5 mt-3 ml-7 text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
                  >
                    <span>View detailed results →</span>
                  </Link>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <p className="text-sm font-medium text-red-800">Simulation failed: {simResult.error}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
