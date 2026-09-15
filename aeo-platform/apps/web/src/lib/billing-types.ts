export type PlanFeature = {
  name: string;
  included: boolean;
};

export type Plan = {
  name: string;
  display_name: string;
  description: string;
  monthly_tasks: number | null;
  max_users: number;
  features: string[];
  price_monthly: number;
  price_yearly: number;
  stripe_price_monthly: string | null;
  stripe_price_yearly: string | null;
  popular?: boolean;
};

export type Subscription = {
  id: string;
  stripe_subscription_id: string;
  status: string;
  plan: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
};

export type BillingSubscriptionResponse = {
  has_subscription: boolean;
  subscription: Subscription | null;
};

export type Invoice = {
  id: string;
  stripe_invoice_id: string;
  status: string;
  amount_due: number;
  currency: string;
  period_start: string | null;
  period_end: string | null;
  paid_at: string | null;
  invoice_pdf: string | null;
  hosted_invoice_url: string | null;
};

export type BillingInvoicesResponse = {
  items: Invoice[];
  total: number;
};

export type CheckoutResponse = {
  checkout_url: string;
};

export type PortalResponse = {
  portal_url: string;
};
