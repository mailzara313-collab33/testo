export interface Account {
  id: number;
  customer_id: string;
  name: string;
  currency_code: string;
  is_manager: boolean;
  is_active: boolean;
  label?: string;
  synced_at?: string;
}

export interface Campaign {
  campaign_id: string;
  campaign_name: string;
  campaign_type: string;
  status: string;
  cost: number;
  impressions: number;
  clicks: number;
  conversions: number;
  conversion_value: number;
  ctr: number;
  cpc: number;
  cpa: number;
  roas: number;
  daily_budget?: number;
  avg_quality_score?: number;
}

export interface KPIData {
  value: number;
  previous_value: number;
  change_pct: number;
}

export interface DashboardKPIs {
  cost: KPIData;
  conversions: KPIData;
  conversion_value: KPIData;
  roas: KPIData;
  cpa: KPIData;
  ctr: KPIData;
  cpc: KPIData;
  impressions: KPIData;
  clicks: KPIData;
}

export interface TimeSeriesPoint {
  date: string;
  cost: number;
  conversions: number;
  clicks: number;
  impressions: number;
  roas: number;
}

export interface CampaignSpendShare {
  campaign_name: string;
  campaign_id: string;
  cost: number;
  pct: number;
}

export interface HeatmapCell {
  day: number;
  hour: number;
  value: number;
}

export interface DashboardData {
  kpis: DashboardKPIs;
  time_series: TimeSeriesPoint[];
  spend_by_campaign: CampaignSpendShare[];
  hourly_heatmap: HeatmapCell[];
  date_from: string;
  date_to: string;
}

export interface AutomationRule {
  id: number;
  name: string;
  description?: string;
  status: string;
  is_dry_run: boolean;
  condition_json: string;
  action_json: string;
  schedule: string;
  run_count: number;
}

export interface Alert {
  id: number;
  account_id?: string;
  severity: "info" | "warning" | "critical";
  title: string;
  message: string;
  is_read: boolean;
}
