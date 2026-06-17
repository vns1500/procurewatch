const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Tender {
  id: string;
  gem_id: string;
  title: string;
  ministry: string;
  state: string;
  value: number;
  tender_date: string;
  close_date: string;
  bid_count: number;
  risk_score: number;
  anomaly_flags: string[];
  vendor_name: string | null;
  created_at: string;
}

export interface TenderListResponse {
  tenders: Tender[];
  total: number;
  page: number;
  limit: number;
}

export interface MinistryRisk {
  ministry: string;
  count: number;
  total_value: number;
}

export interface AnomalyBreakdown {
  type: string;
  count: number;
}

export interface StateRisk {
  state: string;
  risk_score: number;
  flagged_count: number;
}

export interface DashboardStats {
  flagged_this_month: number;
  suspicious_value: number;
  new_anomalies_today: number;
  total_tenders_scanned: number;
  top_risky_ministries: MinistryRisk[];
  anomaly_breakdown: AnomalyBreakdown[];
  state_risk_map: StateRisk[];
}

export interface TenderFilters {
  ministry?: string;
  state?: string;
  risk_min?: number;
  risk_max?: number;
  anomaly_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}

// Vendors
export interface VendorSummary {
  id: string;
  name: string;
  gstin: string | null;
  state: string | null;
  total_wins: number;
  total_value: number;
  win_rate: number;
  risk_level: string;
}

export interface ContractSummary {
  tender_id: string;
  title: string;
  value: number;
  date: string;
  risk_score: number;
  anomaly_flags: string[];
}

export interface VendorProfile extends VendorSummary {
  incorporation_date: string | null;
  mca_verified: boolean;
  recent_contracts: ContractSummary[];
}

export interface VendorListResponse {
  vendors: VendorSummary[];
  total: number;
  page: number;
  limit: number;
}

// Anomalies
export interface AnomalyDetail {
  id: string;
  type: string;
  severity: string;
  evidence: Record<string, unknown> | null;
  detected_at: string;
  status: string;
  tender_id: string;
  tender_title: string;
  ministry: string;
  risk_score: number;
}

export interface AnomalyListResponse {
  anomalies: AnomalyDetail[];
  total: number;
  page: number;
  limit: number;
}

// Reports
export interface ReportSummary {
  id: string;
  title: string | null;
  risk_level: string | null;
  report_type: string;
  tender_count: number;
  created_at: string;
  summary_preview: string | null;
  status: string;
}

export interface RedFlag {
  flag: string;
  description: string;
  severity: string;
}

export interface ReportSections {
  executive_summary: string;
  red_flags: RedFlag[];
  evidence_analysis: string;
  comparative_analysis: string;
  rti_questions: string[];
  recommended_actions: string[];
  estimated_loss: string;
}

export interface ReportDetail {
  id: string;
  title: string | null;
  risk_level: string | null;
  report_type: string;
  sections: ReportSections | null;
  raw_markdown: string | null;
  created_at: string;
  status: string;
}

// Auth / Billing
export interface User {
  email: string;
  plan: string;
  reports_used_this_month: number;
  api_key: string;
  is_admin: boolean;
}

export interface CheckoutResponse {
  checkout_url: string;
}

// Network graph
export interface NetworkNode {
  id: string;
  type: "vendor" | "director";
  label: string;
  risk_level?: string;
  din?: string;
}

export interface NetworkEdge {
  source: string;
  target: string;
  type: string;
}

export interface VendorNetwork {
  vendor_id: string;
  vendor_name: string;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

// Detection
export interface DetectionRunResponse {
  status: string;
  task_id: string;
  message: string;
}

// Alerts
export interface AlertSummary {
  id: string;
  ministries: string[];
  keywords: string[];
  email: string;
  status: string;
  last_triggered: string | null;
  trigger_count: number;
  created_at: string;
}

async function fetchJSON<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    });
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function patchJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchJSON<DashboardStats>("/dashboard/stats");
}

export async function getTenders(filters: TenderFilters = {}): Promise<TenderListResponse> {
  return fetchJSON<TenderListResponse>("/tenders", {
    ministry: filters.ministry,
    state: filters.state,
    risk_min: filters.risk_min,
    risk_max: filters.risk_max,
    anomaly_type: filters.anomaly_type,
    date_from: filters.date_from,
    date_to: filters.date_to,
    page: filters.page ?? 1,
    limit: filters.limit ?? 20,
  });
}

export async function getVendors(params: {
  state?: string;
  risk_level?: string;
  page?: number;
  limit?: number;
} = {}): Promise<VendorListResponse> {
  return fetchJSON<VendorListResponse>("/vendors", {
    state: params.state,
    risk_level: params.risk_level,
    page: params.page ?? 1,
    limit: params.limit ?? 20,
  });
}

export async function getVendor(id: string): Promise<VendorProfile> {
  return fetchJSON<VendorProfile>(`/vendors/${id}`);
}

export async function getAnomalies(params: {
  type?: string;
  severity?: string;
  ministry?: string;
  date_from?: string;
  page?: number;
  limit?: number;
} = {}): Promise<AnomalyListResponse> {
  return fetchJSON<AnomalyListResponse>("/anomalies", {
    type: params.type,
    severity: params.severity,
    ministry: params.ministry,
    date_from: params.date_from,
    page: params.page ?? 1,
    limit: params.limit ?? 20,
  });
}

export async function getReports(): Promise<ReportSummary[]> {
  return fetchJSON<ReportSummary[]>("/reports");
}

export async function generateReport(
  tenderIds: string[],
  reportType: "quick" | "full" = "full",
): Promise<{ report_id: string; status: string }> {
  return postJSON("/reports/generate", { tender_ids: tenderIds, report_type: reportType });
}

export async function getReport(id: string): Promise<ReportDetail> {
  return fetchJSON<ReportDetail>(`/reports/${id}`);
}

export async function deleteReport(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw new Error(`API error ${res.status}`);
}

export async function exportReportPdf(id: string): Promise<void> {
  const url = `${API_BASE}/export/reports/${id}/pdf`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `procurewatch_report_${id.slice(0, 8)}.pdf`;
  a.click();
}

export async function registerUser(email: string): Promise<{ api_key: string; email: string; plan: string }> {
  return postJSON("/auth/register", { email });
}

export async function getMe(apiKey: string): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { "X-API-Key": apiKey },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<User>;
}

export async function createCheckoutSession(data: {
  plan: string;
  email?: string;
  success_url: string;
  cancel_url: string;
}): Promise<CheckoutResponse> {
  return postJSON("/billing/create-checkout-session", data);
}

export async function deleteAlert(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/alerts/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) throw new Error(`API error ${res.status}`);
}

export async function getAlerts(): Promise<AlertSummary[]> {
  return fetchJSON<AlertSummary[]>("/alerts");
}

export async function subscribeAlert(data: {
  ministries: string[];
  keywords: string[];
  email: string;
}): Promise<{ alert_id: string }> {
  return postJSON("/alerts/subscribe", data);
}

export async function patchAlert(id: string, status: "active" | "paused"): Promise<AlertSummary> {
  return patchJSON<AlertSummary>(`/alerts/${id}`, { status });
}

export async function getVendorNetwork(id: string): Promise<VendorNetwork> {
  return fetchJSON<VendorNetwork>(`/vendors/${id}/network`);
}

export async function patchAnomaly(id: string, status: string): Promise<AnomalyDetail> {
  return patchJSON<AnomalyDetail>(`/anomalies/${id}`, { status });
}

export async function runDetection(): Promise<DetectionRunResponse> {
  return postJSON<DetectionRunResponse>("/detection/run", {});
}

export function formatRupees(paise: number): string {
  const rupees = paise / 100;
  if (rupees >= 1_00_00_000) return `₹${(rupees / 1_00_00_000).toFixed(2)}Cr`;
  if (rupees >= 1_00_000) return `₹${(rupees / 1_00_000).toFixed(2)}L`;
  if (rupees >= 1_000) return `₹${(rupees / 1_000).toFixed(1)}K`;
  return `₹${rupees.toFixed(0)}`;
}

export function riskLevelColor(level: string): string {
  switch (level) {
    case "critical": return "var(--accent-red)";
    case "high": return "var(--accent-red)";
    case "medium": return "var(--accent-amber)";
    default: return "var(--accent-green)";
  }
}

export function severityBorderColor(severity: string): string {
  switch (severity) {
    case "critical":
    case "high": return "var(--accent-red)";
    case "medium": return "var(--accent-amber)";
    default: return "var(--accent-green)";
  }
}
