export type Ticket = {
  id: string;
  customer: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  summary: string;
  product: string;
};

export const tickets: Ticket[] = [
  {
    id: 'INC-1048',
    customer: 'Acme Retail',
    priority: 'urgent',
    product: 'Checkout API',
    summary: 'Payment authorization succeeds but order confirmation emails are delayed.',
  },
  {
    id: 'INC-1052',
    customer: 'Northwind Traders',
    priority: 'normal',
    product: 'Admin Console',
    summary: 'Saved filters are not visible after refreshing the reports page.',
  },
  {
    id: 'INC-1057',
    customer: 'Contoso Health',
    priority: 'high',
    product: 'Webhook Delivery',
    summary: 'Endpoint receives duplicate delivery attempts after a successful 200 response.',
  },
];

export function findTicket(id: string) {
  return tickets.find(ticket => ticket.id.toLowerCase() === id.toLowerCase()) ?? null;
}
