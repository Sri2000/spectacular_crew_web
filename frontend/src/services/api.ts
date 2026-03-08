import axios from 'axios';

const API_BASE_URL = ''; // Use relative URLs → Vite proxy routes /api/* to http://localhost:8000

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to headers if available
const token = localStorage.getItem('token');
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// Always attach the latest token from localStorage, and strip Content-Type for FormData
// so the browser can set the correct multipart boundary automatically.
api.interceptors.request.use(config => {
  const latestToken = localStorage.getItem('token');
  if (latestToken) {
    config.headers['Authorization'] = `Bearer ${latestToken}`;
  }
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

// Authentication
export const login = async (username: string, password: string) => {
  const response = await api.post('/api/auth/login', { username, password });
  return response.data;
};

export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export interface RiskAssessment {
  id: string;
  product_category: string;
  risk_score: number;
  risk_type: string;
  confidence_level: number;
  detection_timestamp: string;
  contributing_factors?: string[];
  historical_comparison?: Record<string, number>;
}

export interface FailureScenario {
  scenario_id: string;
  scenario_type: string;
  affected_products: string[];
  time_horizon: number;
  initial_conditions?: Record<string, any>;
  simulation_parameters?: Record<string, number>;
  created_timestamp: string;
}

export interface SimulationResult {
  result_id: string;
  scenario_id: string;
  simulation_data: any;
  inventory_levels?: Record<string, number[]>;
  stockout_probabilities?: Record<string, number>;
  overstock_costs?: Record<string, number>;
  execution_time_seconds?: number;
  simulation_timestamp: string;
}

export interface PropagationScore {
  id: string;
  scenario_id: string;
  overall_score: number;
  function_impacts: Record<string, number>;
  cascade_depth: number;
  affected_business_units?: string[];
  calculation_timestamp: string;
  confidence_metrics?: Record<string, number>;
}

export interface ExecutiveSummary {
  summary_id: string;
  scenario_id: string;
  revenue_risk: string;
  market_reason: string;
  urgency_level: string;
  recommended_actions?: string[];
  trade_offs?: Record<string, string>;
  generated_timestamp: string;
}

export interface MitigationStrategy {
  strategy_id: string;
  scenario_id: string;
  strategy_name: string;
  description: string;
  effectiveness_score: number;
  implementation_complexity: string;
  resource_requirements?: Record<string, any>;
  timeline_days: number;
  cost_estimate?: number;
  trade_offs?: string[];
}

// Data Ingestion
export const uploadCSV = async (dataType: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  // Do NOT set Content-Type manually — the browser must set it automatically
  // so it includes the multipart boundary (e.g. "multipart/form-data; boundary=----xyz").
  // Without the boundary, python-multipart can't parse the body and drops the connection.
  const response = await api.post(`/api/data/upload/csv/${dataType}`, formData);
  return response.data;
};

export const uploadJSON = async (dataType: string, data: any) => {
  const response = await api.post(`/api/data/upload/json/${dataType}`, data);
  return response.data;
};

// Risk Analysis
export const analyzeRisks = async (marketData: any) => {
  const response = await api.post('/api/analysis/risk/analyze', marketData);
  return response.data;
};

export const getRisks = async (): Promise<RiskAssessment[]> => {
  const response = await api.get('/api/analysis/risks');
  return response.data;
};

// Scenario Simulation
export const simulateScenario = async (scenarioData: any) => {
  const response = await api.post('/api/analysis/simulate', scenarioData);
  return response.data;
};

export const getScenarios = async (): Promise<FailureScenario[]> => {
  const response = await api.get('/api/analysis/scenarios');
  return response.data;
};

export const getScenarioDetails = async (scenarioId: string) => {
  const response = await api.get(`/api/analysis/scenarios/${scenarioId}`);
  return response.data;
};

// Stock Transfer Optimization
export interface StoreCategoryStat {
  store_id: string;
  region: string;
  product_category: string;
  avg_stock_level: number;
  avg_demand: number;
  avg_price: number;
  avg_holding_cost: number;
  stockout_rate: number;
  overstock_rate: number;
  avg_lost_sales_units: number;
  total_revenue: number;
  fulfillment_rate: number;
}

export interface TransferEconomics {
  saved_holding_cost: number;
  saved_procurement_cost: number;
  transport_cost: number;
  net_benefit: number;
  roi_percent: number;
}

export interface TransferStore {
  store_id: string;
  region: string;
  avg_stock_level: number;
  avg_demand: number;
  excess_units?: number;
  deficit_units?: number;
  avg_holding_cost?: number;
  avg_lost_sales_units?: number;
}

export interface TransferRecommendation {
  transfer_id: string;
  product_category: string;
  source_store: TransferStore;
  destination_store: TransferStore;
  transfer_quantity: number;
  economics: TransferEconomics;
  recommendation_strength: 'Strong' | 'Moderate' | 'Marginal' | 'Not Viable';
  is_viable: boolean;
  priority_rank: number;
}

export interface TransferResult {
  success: boolean;
  total_opportunities: number;
  viable_transfers: number;
  total_potential_savings: number;
  stores_involved: number;
  transport_cost_per_unit: number;
  time_horizon_days: number;
  transfers: TransferRecommendation[];
}

export const recommendTransfers = async (
  store_stats: StoreCategoryStat[],
  transport_cost_per_unit: number,
  time_horizon_days: number = 30,
): Promise<TransferResult> => {
  const response = await api.post('/api/transfers/recommend', {
    store_stats,
    transport_cost_per_unit,
    time_horizon_days,
  });
  return response.data;
};

export default api;
