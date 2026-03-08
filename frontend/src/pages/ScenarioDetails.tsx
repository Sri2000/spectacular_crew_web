import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getScenarioDetails } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ArrowLeft, Package, Clock, Hash, Layers, CheckCircle, ChevronRight, Sparkles, Bot } from 'lucide-react';

export default function ScenarioDetails() {
  const { id } = useParams<{ id: string }>();
  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadDetails(id);
  }, [id]);

  const loadDetails = async (scenarioId: string) => {
    try {
      const data = await getScenarioDetails(scenarioId);
      setDetails(data);
    } catch (error) {
      console.error('Error loading scenario details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplexityColor = (complexity: string) => {
    if (complexity === 'High') return 'text-red-600 bg-red-50 ring-red-200';
    if (complexity === 'Medium') return 'text-amber-600 bg-amber-50 ring-amber-200';
    return 'text-emerald-600 bg-emerald-50 ring-emerald-200';
  };

  const getScoreColor = (score: number) => {
    const pct = (score / 10) * 100;
    if (pct >= 70) return '#ef4444';
    if (pct >= 40) return '#f59e0b';
    return '#10b981';
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-gray-200 rounded-xl w-72" />
        <div className="bg-white rounded-2xl h-32 shadow-card" />
        <div className="bg-white rounded-2xl h-80 shadow-card" />
      </div>
    );
  }

  if (!details) {
    return (
      <div className="bg-white rounded-2xl shadow-card border border-gray-100 py-20 text-center">
        <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Package className="h-8 w-8 text-gray-300" />
        </div>
        <h3 className="text-base font-semibold text-gray-700 mb-1">Scenario Not Found</h3>
        <p className="text-sm text-gray-400">The requested scenario could not be found</p>
        <Link to="/" className="inline-flex items-center space-x-1.5 mt-4 text-sm font-medium text-indigo-600 hover:text-indigo-700">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    );
  }

  const chartData = details.simulation?.simulation_data?.[0]?.data?.map((d: any) => ({
    day: d.day,
    inventory: d.inventory,
    demand: d.demand,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link to="/" className="inline-flex items-center space-x-1.5 text-sm text-gray-400 hover:text-indigo-600 transition-colors mb-3">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Link>
        <h2 className="text-2xl font-bold text-gray-900">Scenario Details</h2>
        <p className="mt-0.5 text-sm text-gray-500">
          {details.scenario.scenario_type.replace(/_/g, ' ')} &middot; {details.scenario.time_horizon} day horizon
        </p>
      </div>

      {/* Scenario Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Scenario ID', value: details.scenario.scenario_id.slice(0, 8) + '...', icon: Hash, iconBg: 'bg-indigo-50', iconColor: 'text-indigo-500' },
          { label: 'Type', value: details.scenario.scenario_type.replace(/_/g, ' '), icon: Layers, iconBg: 'bg-violet-50', iconColor: 'text-violet-500' },
          { label: 'Products', value: `${details.scenario.affected_products.length} affected`, icon: Package, iconBg: 'bg-amber-50', iconColor: 'text-amber-500' },
          { label: 'Time Horizon', value: `${details.scenario.time_horizon} days`, icon: Clock, iconBg: 'bg-emerald-50', iconColor: 'text-emerald-500' },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="bg-white rounded-2xl shadow-card border border-gray-100 p-4">
              <div className={`w-9 h-9 ${item.iconBg} rounded-xl flex items-center justify-center mb-3`}>
                <Icon className={`h-4.5 w-4.5 ${item.iconColor}`} style={{ width: '18px', height: '18px' }} />
              </div>
              <p className="text-xs text-gray-400 font-medium">{item.label}</p>
              <p className="text-sm font-semibold text-gray-800 mt-0.5">{item.value}</p>
            </div>
          );
        })}
      </div>

      {/* Simulation Chart */}
      {details.simulation && chartData.length > 0 && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-900">Simulation Results</h3>
            <p className="text-xs text-gray-400 mt-0.5">Inventory vs demand over time</p>
          </div>
          <div className="p-6">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="day"
                    label={{ value: 'Days', position: 'insideBottom', offset: -12, fontSize: 12, fill: '#94a3b8' }}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                    tickLine={false}
                  />
                  <YAxis
                    label={{ value: 'Units', angle: -90, position: 'insideLeft', offset: 10, fontSize: 12, fill: '#94a3b8' }}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', fontSize: '12px' }}
                    labelStyle={{ fontWeight: 600, color: '#1e293b' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '16px' }} />
                  <Line type="monotone" dataKey="inventory" stroke="#6366f1" strokeWidth={2.5} dot={false} name="Inventory Level" activeDot={{ r: 5, fill: '#6366f1' }} />
                  <Line type="monotone" dataKey="demand" stroke="#f59e0b" strokeWidth={2.5} dot={false} name="Daily Demand" activeDot={{ r: 5, fill: '#f59e0b' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Impact Analysis */}
      {details.impact && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-900">Impact Analysis</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {/* Overall score first */}
              <div className="bg-red-50 rounded-xl p-4 border border-red-100">
                <p className="text-xs font-medium text-red-500 mb-2 uppercase tracking-wide">Overall</p>
                <p className="text-2xl font-bold text-red-700">{details.impact.overall_score}<span className="text-sm font-medium text-red-400">/10</span></p>
                <div className="w-full h-1.5 bg-red-100 rounded-full overflow-hidden mt-2">
                  <div className="h-full bg-red-500 rounded-full" style={{ width: `${(details.impact.overall_score / 10) * 100}%` }} />
                </div>
              </div>

              {Object.entries(details.impact.function_impacts).map(([func, impact]: [string, any]) => {
                const color = getScoreColor(impact);
                return (
                  <div key={func} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <p className="text-xs font-medium text-gray-500 capitalize mb-2">{func}</p>
                    <p className="text-2xl font-bold text-gray-800">{impact.toFixed(1)}</p>
                    <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden mt-2">
                      <div className="h-full rounded-full transition-all" style={{ width: `${(impact / 10) * 100}%`, backgroundColor: color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* AI Reasoning & Explainability */}
      {details.summary?.explanation && (
        <div className="bg-white rounded-2xl shadow-card border border-violet-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-violet-100 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-violet-50">
                <Sparkles className="h-5 w-5 text-violet-600" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">AI Reasoning & Explainability</h3>
                <p className="text-xs text-gray-400 mt-0.5">Auditable decision support</p>
              </div>
            </div>
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-violet-50 text-violet-600 ring-1 ring-violet-200">
              <Bot className="h-3 w-3" />
              <span>{details.summary.generated_by === 'gemini' ? 'Gemini AI' : 'Rule-based'}</span>
            </span>
          </div>
          <div className="p-6">
            <p className="text-sm text-gray-700 leading-relaxed">{details.summary.explanation}</p>
            {details.summary.trade_offs && Object.keys(details.summary.trade_offs).length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Decision Trade-offs</p>
                <div className="space-y-2">
                  {Object.entries(details.summary.trade_offs).map(([option, tradeoff]: [string, any]) => (
                    <div key={option} className="flex items-start space-x-2">
                      <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md flex-shrink-0 mt-0.5">{option}</span>
                      <span className="text-xs text-gray-500">{tradeoff}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mitigation Strategies */}
      {details.strategies && details.strategies.length > 0 && (
        <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-base font-semibold text-gray-900">Mitigation Strategies</h3>
            <span className="text-xs text-gray-400">{details.strategies.length} strategies</span>
          </div>
          <div className="p-4 space-y-3">
            {details.strategies.map((strategy: any, index: number) => (
              <div key={strategy.strategy_id} className="flex items-start space-x-4 p-4 rounded-xl border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/20 transition-all group">
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
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ring-1 ${getComplexityColor(strategy.implementation_complexity)}`}>
                      {strategy.implementation_complexity}
                    </span>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-1" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
