import { useCallback, useContext, useMemo } from 'react';
import { CheckoutStore } from '../store';
import * as api from '../api';
import { handleError, OrderError } from '../utils';

const useDiscount = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;
  const discounts = state.applicationState?.discounts;
  const memoizedDiscounts = useMemo(() => discounts, [JSON.stringify(discounts)]);
  const discountLoadingStatus = state.loadingStatus.discount;
  const discountErrors = state.errors.discount;
  const memoizedDiscountErrors = useMemo(() => discountErrors, [JSON.stringify(discountErrors)]);

  const applyDiscount = useCallback(async (discount) => {
    dispatch({
      type: 'checkout/discount/adding',
    });

    try {
      const response = await api.addDiscount(token, apiPath, discount);
      const error = handleError('discount', response);
      if (error) {
        if (onError) {
          onError(error.error);
        }

        dispatch({
          type: `checkout/${error.type}/setErrors`,
          payload: error.payload,
        });

        return Promise.reject(error.error);
      }

      dispatch({
        type: 'checkout/discount/added',
      });

      dispatch({
        type: 'checkout/update',
        payload: response.data.application_state,
      });

      return Promise.resolve(response);
    } catch (e) {
      if (onError) {
        onError(e);
      }

      dispatch({
        type: 'checkout/order/setErrors',
        payload: [{
          field: 'order',
          message: 'An error with your order has occured, please try again',
        }],
      });

      return Promise.reject(new OrderError());
    }
  }, [onError]);

  const removeDiscount = useCallback(async (code) => {
    dispatch({
      type: 'checkout/discount/removing',
    });

    try {
      const response = await api.removeDiscount(token, apiPath, code);
      const error = handleError('discount', response);
      if (error) {
        if (onError) {
          onError(error.error);
        }

        dispatch({
          type: `checkout/${error.type}/setErrors`,
          payload: error.payload,
        });

        return Promise.reject(error.error);
      }

      dispatch({
        type: 'checkout/discount/removed',
      });

      dispatch({
        type: 'checkout/update',
        payload: response.data.application_state,
      });

      return Promise.resolve(response);
    } catch (e) {
      if (onError) {
        onError(e);
      }

      dispatch({
        type: 'checkout/order/setErrors',
        payload: [{
          field: 'order',
          message: 'An error with your order has occured, please try again',
        }],
      });

      return Promise.reject(new OrderError());
    }
  }, [onError]);

  return {
    data: {
      discounts: memoizedDiscounts,
      /**
       * @deprecated
       */
      discountApplied: discounts?.length > 0,
      /**
       * @deprecated
       */
      discountCode: discounts[0]?.code ?? '',
      /**
       * @deprecated
       */
      discountTotal: discounts[0]?.value ?? 0,
    },
    errors: memoizedDiscountErrors,
    loadingStatus: discountLoadingStatus,
    applyDiscount,
    removeDiscount,
  };
};

export default useDiscount;
