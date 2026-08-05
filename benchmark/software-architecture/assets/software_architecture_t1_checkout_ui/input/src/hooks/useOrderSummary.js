import { useContext, useMemo } from 'react';
import { CheckoutStore } from '../store';

const useOrderSummary = () => {
  const { state } = useContext(CheckoutStore);
  const { customer, payments } = state.applicationState;
  const shippingAddress = state.applicationState.addresses.shipping;
  const billingAddress = state.applicationState.addresses.billing;
  const selectedShipping = state.applicationState.shipping.selected_shipping;

  const memoizedCustomer = useMemo(() => customer, [JSON.stringify(customer)]);
  const memoizedShippingAddress = useMemo(() => shippingAddress, [JSON.stringify(shippingAddress)]);
  const memoizedBillingAddress = useMemo(() => billingAddress, [JSON.stringify(billingAddress)]);
  const memoizedSelectedShipping = useMemo(() => selectedShipping, [JSON.stringify(selectedShipping)]);
  const memoizedPayments = useMemo(() => payments, [JSON.stringify(payments)]);

  return {
    data: {
      customer: memoizedCustomer,
      shippingAddress: memoizedShippingAddress,
      billingAddress: memoizedBillingAddress,
      selectedShipping: memoizedSelectedShipping,
      payments: memoizedPayments,
    },
  };
};

export default useOrderSummary;
