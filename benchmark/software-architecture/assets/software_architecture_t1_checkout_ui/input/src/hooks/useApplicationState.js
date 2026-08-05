import { useContext } from 'react';
import { CheckoutStore } from '../store';

const useApplicationState = () => {
  const { state, dispatch } = useContext(CheckoutStore);

  const setApplicationStatus = (newState) => {
    dispatch({
      type: 'checkout/update',
      payload: newState,
    });
  };

  return {
    data: state,
    updateApplicationState: setApplicationStatus,
  };
};

export default useApplicationState;
