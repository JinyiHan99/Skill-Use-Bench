import { useContext } from 'react';
import { CheckoutStore } from '../store';

const useLoadingStatus = () => {
  const { state } = useContext(CheckoutStore);

  return {
    data: state.loadingStatus,
  };
};

export default useLoadingStatus;
