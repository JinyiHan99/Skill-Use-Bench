import { useCallback, useContext } from 'react';
import { CheckoutStore } from '../store';
import { OrderError } from '../utils';

const useErrors = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);

  const setOrderError = useCallback(async (message = 'An error with your order has occurred, please try again') => {
    if (onError) {
      onError(new OrderError());
    }
    return dispatch({
      type: 'checkout/order/setErrors',
      payload: [{
        field: 'order',
        message: message,
      }]
    });
  }, [onError]);

  const clearOrderError = useCallback(async () => {
    return dispatch({
      type: 'checkout/order/clearErrors',
    });
  })

  return {
    data: state.errors,
    setOrderError,
    clearOrderError
  };
};

export default useErrors;
