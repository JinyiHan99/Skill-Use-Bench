import { useContext, useMemo } from 'react';
import { CheckoutStore } from '../store';

const useBreakdown = () => {
  const { state } = useContext(CheckoutStore);
  const payments = state.applicationState?.payments;
  const shippingDescription = state.applicationState?.shipping?.selected_shipping?.description;
  const memoizedPayments = useMemo(() => payments, [JSON.stringify(payments)]);
  const hasPayments = useMemo(() => payments.length > 0, [JSON.stringify(payments)]);
  const taxes = state.applicationState?.taxes;
  const memoizedTaxes = useMemo(() => taxes, [JSON.stringify(taxes)]);
  const taxesIncluded = taxes[0]?.is_included;

  const {
    subTotal,
    shippingTotal,
    excludedTaxes,
    discountTotal,
    total,
    remainingBalance,
    taxesTotal,
    totalItems,
  } = state.orderTotals;

  const { orderStatus } = state.orderInfo;

  return {
    data: {
      subTotal,
      shippingTotal,
      shippingDescription,
      excludedTaxes,
      discountTotal,
      total,
      remainingBalance,
      taxesTotal,
      totalItems,
      orderStatus,
      payments: memoizedPayments,
      hasPayments,
      taxes: memoizedTaxes,
      taxesIncluded,
    },
  };
};

export default useBreakdown;
