import { createStateStore } from "@json-render/core";

export const initialState = createStateStore({
  filters: {
    timeRange: "7d",
    region: "all",
  },
  activeTab: "overview",
  metrics: {
    totalUsers: 12847,
    activeUsers: 3291,
    revenue: 284500,
    conversionRate: 3.2,
  },
  recentOrders: [
    { id: "ORD-4521", customer: "Alice Chen", total: 129.99, status: "shipped" },
    { id: "ORD-4520", customer: "Bob Martinez", total: 89.50, status: "processing" },
    { id: "ORD-4519", customer: "Carol Jones", total: 245.00, status: "delivered" },
    { id: "ORD-4518", customer: "David Kim", total: 67.25, status: "processing" },
    { id: "ORD-4517", customer: "Eva Müller", total: 312.00, status: "shipped" },
  ],
});
