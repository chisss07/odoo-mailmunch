export type AuthMethod = 'api_key' | 'password'

export interface LoginRequest {
  odoo_url: string
  database: string
  email: string
  api_key?: string
  password?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
}

export interface EmailRecord {
  id: number
  sender: string
  subject: string
  status: string
  classification: string
  source: string
  created_at: string
}

export interface LineItem {
  description: string
  sku: string | null
  quantity: number
  unit_price: number
  confidence: string
  product_odoo_id: number | null
  product_name: string | null
  product_confidence: string
  alternatives: { odoo_id: number; name: string; score: number }[]
}

export interface PODraft {
  id: number
  email_id: number
  vendor_odoo_id: number | null
  vendor_name: string
  vendor_confidence: string
  line_items: LineItem[]
  total_amount: string | null
  expected_date: string | null
  sales_order_id: number | null
  sales_order_name: string | null
  status: string
  created_at: string
}

export interface TrackingInfo {
  tracking_numbers: { number: string; carrier: string; url: string }[]
  estimated_delivery: string | null
}

export interface POTracking {
  id: number
  odoo_po_id: number
  odoo_po_name: string
  vendor_name: string
  status: string
  sales_order_name: string | null
  tracking_info: TrackingInfo | null
  created_at: string
}

export interface SalesOrder {
  id: number
  name: string
  partner_id: [number, string]
  date_order: string
  amount_total: number
  state: string
}
