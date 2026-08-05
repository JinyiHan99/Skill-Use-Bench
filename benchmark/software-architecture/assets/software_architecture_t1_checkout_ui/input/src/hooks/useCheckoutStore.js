import { useContext } from 'react';
import { CheckoutStore } from '../store';

const useCheckoutStore = () => {
  const { state, dispatch } = useContext(CheckoutStore);

  return { state, dispatch };
};

export default useCheckoutStore;
