import { useCallback, useContext, useMemo } from 'react';
import { CheckoutStore } from '../store';
import { updateBillingAddress } from '../api';
import { handleError, OrderError } from '../utils';

const useBillingSameAsShipping = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;
  const shippingAddress = state.applicationState?.addresses?.shipping;
  const billingAddressErrors = state.errors.billingAddress;
  const billingAddressLoadingStatus = state.loadingStatus.billingAddress;
  const memoizedBillingAddressErrors = useMemo(() => billingAddressErrors, [JSON.stringify(billingAddressErrors)]);
  const memoizedShippingAddress = useMemo(() => shippingAddress, [JSON.stringify(shippingAddress)]);
  const { billingSameAsShipping } = state.orderInfo;

  const setBillingSameAsShipping = useCallback(async (value) => {
    dispatch({
      type: 'checkout/billingAddress/setBillingSameAsShipping',
      payload: value,
    });

    if (value) {
      if (memoizedShippingAddress?.country_code) {
        dispatch({
          type: 'checkout/billingAddress/setting',
        });

        try {
          const response = await updateBillingAddress(token, apiPath, memoizedShippingAddress);
          const error = handleError('billingAddress', response);
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
            type: 'checkout/update',
            payload: response.data.application_state,
          });

          dispatch({
            type: 'checkout/billingAddress/set',
            payload: response.data.address,
          });

          return Promise.resolve(response);
        } catch (e) {
          if (onError) {
            onError(e);
          }

          dispatch({
            type: 'checkout/billingAddress/setErrors',
            payload: [{
              field: 'order',
              message: 'An error with your order has occured, please try again',
            }],
          });

          return Promise.reject(new OrderError());
        }
      }
    }

    return Promise.resolve();
  }, [memoizedShippingAddress, onError]);

  return {
    data: billingSameAsShipping,
    errors: memoizedBillingAddressErrors,
    loadingStatus: billingAddressLoadingStatus,
    setBillingSameAsShipping,
  };
};

export default useBillingSameAsShipping;
