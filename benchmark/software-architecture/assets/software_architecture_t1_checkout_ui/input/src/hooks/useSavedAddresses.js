import { useContext, useMemo } from 'react';
import { CheckoutStore } from '../store';

const useSavedAddresses = () => {
  const { state } = useContext(CheckoutStore);
  const savedAddresses = state.applicationState.customer.saved_addresses;
  const memoizedSavedAddresses = useMemo(() => savedAddresses, [JSON.stringify(savedAddresses)]);

  return {
    data: memoizedSavedAddresses,
  };
};

export default useSavedAddresses;
