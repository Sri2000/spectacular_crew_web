/**
 * Enterprise dataset cache — persists ingestion stats in localStorage so the
 * Fleet Dashboard and Store Dashboard can read them without re-uploading.
 *
 * Key: retail_risk_enterprise_cache
 * Written by: StoreTransfer.tsx and DataUpload.tsx after a successful enterprise upload.
 * Read by:    FleetDashboard.tsx and StoreDashboard.tsx on mount.
 */

import { StoreCategoryStat } from '../services/api';

// ── Stat shapes (mirrors backend data_ingestion.py output) ────────────────────

export interface AggregateStats {
  total_records: number;
  date_range: { start: string; end: string; days: number } | null;
  unique_products: number;
  unique_stores: number;
  unique_regions: number;
  unique_categories: number;
  total_revenue: number;
  total_lost_sales_value: number;
  total_holding_cost: number;
  fulfillment_rate: number;   // 0–1
  stockout_rate: number;      // 0–1
  overstock_rate: number;     // 0–1
  avg_seller_quality: number; // 0–1
  promotion_rate: number;     // 0–1
}

export interface CategoryStat {
  product_category: string;
  avg_demand: number;
  demand_cv: number;
  avg_price: number;
  avg_stock_level: number;
  avg_holding_cost: number;
  total_holding_cost: number;
  stockout_rate: number;
  overstock_rate: number;
  avg_lost_sales_units: number;
  lost_sales_value: number;
  avg_seller_quality: number;
  promotion_rate: number;
  total_revenue: number;
  fulfillment_rate: number;
}

export interface RegionStat {
  region: string;
  unique_stores: number;
  avg_demand: number;
  total_revenue: number;
  total_holding_cost: number;
  stockout_rate: number;
  overstock_rate: number;
  avg_lost_sales_units: number;
  lost_sales_value: number;
  avg_seller_quality: number;
  fulfillment_rate: number;
}

export interface EnterpriseCache {
  savedAt: string;                // ISO timestamp
  fileName: string;               // original uploaded filename
  recordsCount: number;
  aggregate: AggregateStats;
  categories: CategoryStat[];
  regions: RegionStat[];
  stores: StoreCategoryStat[];    // flat list: one row per (store_id × product_category)
}

// ── Storage key ───────────────────────────────────────────────────────────────

const CACHE_KEY = 'retail_risk_enterprise_cache';

// ── Public API ────────────────────────────────────────────────────────────────

export function loadEnterpriseCache(): EnterpriseCache | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as EnterpriseCache) : null;
  } catch {
    return null;
  }
}

export function saveEnterpriseCache(cache: EnterpriseCache): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch (e) {
    // Storage quota exceeded — fail silently; dashboards will show empty state
    console.warn('enterpriseCache: localStorage write failed', e);
  }
}

export function clearEnterpriseCache(): void {
  localStorage.removeItem(CACHE_KEY);
}
