import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getRisks, getScenarios, RiskAssessment, FailureScenario } from '../services/api';
import { AlertCircle, TrendingUp, Package, Activity, ChevronRight, RefreshCw, Clock } from 'lucide-react';

export default function AnalystDashboard() {
  const [risks, setRisks] = useState<RiskAssessment[]>([]);
  const [scenarios, setScenarios] = useState<FailureScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async (manual = false) => {
    if (manual) setRefreshing(true);
    try {
      const [risksData, scenariosData] = await Promise.all([
        getRisks(),
        getScenarios(),
      ]);
      setRisks(risksData);
      setScenarios(scenariosData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
      if (manual) setRefreshing(false);
    }
  };

  const getRiskScoreStyle = (score: number) => {
    if (score >= 0.8) return { bg: 'bg-red-50', text: 'text-red-600', bar: '#ef4444' };
    if (score >= 0.6) return { bg: 'bg-amber-50', text: 'text-amber-600', bar: '#f59e0b' };
    return { bg: 'bg-emerald-50', text: 'text-emerald-600', bar: '#10b981' };
  };

  const getRiskBadgeStyle = (type: string) => {
    const styles: Record<string, string> = {
      SEASONAL_MISMATCH: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
      OVERSTOCK: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
      STOCKOUT: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    };
    return styles[type] || 'bg-gray-50 text-gray-700 ring-1 ring-gray-200';
  };

  const highRiskCount = risks.filter(r => r.risk_score >= 0.7).length;
  const avgScore = risks.length > 0
    ? (risks.reduce((sum, r) => sum + r.risk_score, 0) / risks.length)
    : 0;

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-gray-200 rounded-xl w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl h-32 shadow-card" />
          ))}
        </div>
        <div className="bg-white rounded-2xl h-64 shadow-card" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analyst Dashboard</h2>
          <p className="mt-0.5 text-sm text-gray-500">
            Monitor retail risks and failure scenarios in real-time
          </p>
        </div>
        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all shadow-card disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Active Risks */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5 hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-start justify-between">
            <div className="w-11 h-11 bg-red-50 rounded-xl flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-red-500" />
            </div>
            <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-full">Live</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-4">{risks.length}</p>
          <p className="text-sm text-gray-500 mt-1">Active Risks</p>
        </div>

        {/* Scenarios */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5 hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-start justify-between">
            <div className="w-11 h-11 bg-indigo-50 rounded-xl flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-indigo-500" />
            </div>
            <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-full">Total</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-4">{scenarios.length}</p>
          <p className="text-sm text-gray-500 mt-1">Scenarios</p>
        </div>

        {/* High Risk */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5 hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-start justify-between">
            <div className="w-11 h-11 bg-amber-50 rounded-xl flex items-center justify-center">
              <Package className="h-5 w-5 text-amber-500" />
            </div>
            <span className="text-xs font-medium bg-amber-50 text-amber-600 px-2 py-1 rounded-full">≥ 70%</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-4">{highRiskCount}</p>
          <p className="text-sm text-gray-500 mt-1">High Risk</p>
        </div>

        {/* Avg Risk Score */}
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-5 hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-start justify-between">
            <div className="w-11 h-11 bg-violet-50 rounded-xl flex items-center justify-center">
              <Activity className="h-5 w-5 text-violet-500" />
            </div>
            <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-full">Avg</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-4">{(avgScore * 100).toFixed(0)}%</p>
          <p className="text-sm text-gray-500 mt-1">Risk Score</p>
        </div>
      </div>

      {/* Risk Assessments Table */}
      <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-gray-900">Risk Assessments</h3>
            <p className="text-xs text-gray-400 mt-0.5">Top {Math.min(risks.length, 10)} of {risks.length} risks</p>
          </div>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600">
            {risks.length} total
          </span>
        </div>
        <div className="overflow-x-auto">
          {risks.length === 0 ? (
            <div className="py-16 text-center">
              <AlertCircle className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No risk data available yet</p>
            </div>
          ) : (
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50/80 border-b border-gray-100">
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Risk Type</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {risks.slice(0, 10).map((risk, idx) => {
                  const style = getRiskScoreStyle(risk.risk_score);
                  return (
                    <tr key={risk.id} className={`hover:bg-indigo-50/30 transition-colors ${idx % 2 === 0 ? '' : 'bg-gray-50/30'}`}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-800">
                        {risk.product_category}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-full ${getRiskBadgeStyle(risk.risk_type)}`}>
                          {risk.risk_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex items-center px-2.5 py-1 text-xs font-bold rounded-full ${style.bg} ${style.text}`}>
                            {(risk.risk_score * 100).toFixed(0)}%
                          </span>
                          <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all" style={{ width: `${risk.risk_score * 100}%`, backgroundColor: style.bar }} />
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-1.5">
                          <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${risk.confidence_level * 100}%` }} />
                          </div>
                          <span className="text-xs font-medium text-gray-500">{(risk.confidence_level * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-1.5 text-xs text-gray-400">
                          <Clock className="h-3 w-3" />
                          <span>{new Date(risk.detection_timestamp).toLocaleString()}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Recent Scenarios */}
      <div className="bg-white rounded-2xl shadow-card border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-gray-900">Recent Scenarios</h3>
            <p className="text-xs text-gray-400 mt-0.5">Latest simulation runs</p>
          </div>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600">
            {scenarios.length} total
          </span>
        </div>
        <div className="p-4">
          {scenarios.length === 0 ? (
            <div className="py-12 text-center">
              <TrendingUp className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No scenarios yet — run a simulation to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {scenarios.slice(0, 5).map((scenario) => (
                <Link
                  key={scenario.scenario_id}
                  to={`/scenario/${scenario.scenario_id}`}
                  className="flex items-center p-4 rounded-xl border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/30 hover:shadow-sm transition-all group"
                >
                  <div className="w-1 h-10 rounded-full bg-indigo-400 mr-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-gray-800 group-hover:text-indigo-700 transition-colors">
                      {scenario.scenario_type.replace(/_/g, ' ')}
                    </h4>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {scenario.affected_products.length} products &middot; {scenario.time_horizon} day horizon
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 flex-shrink-0">
                    <span className="text-xs text-gray-400">
                      {new Date(scenario.created_timestamp).toLocaleDateString()}
                    </span>
                    <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
