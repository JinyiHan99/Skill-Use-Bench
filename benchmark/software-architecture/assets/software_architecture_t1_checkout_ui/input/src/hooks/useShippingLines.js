import { useCallback, useContext, useMemo } from 'react';
import { fetchShippingLines, setShippingLine } from '../api';
import { CheckoutStore } from '../store';
import { handleError, OrderError } from '../utils';

const useShippingLines = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath, applicationState } = state;
  const shippingLines = applicationState.shipping.available_shipping_lines;
  const selectedCountryCode = applicationState?.addresses?.shipping?.country_code;
  const shippingLinesLoadingStatus = state.loadingStatus.shippingLines;
  const selectedShippingLineIndex = parseInt(applicationState.shipping?.selected_shipping?.id ?? 0, 10);
  const selectedShippingAmount = applicationState.shipping?.selected_shipping?.amount;
  const selectedShippingDescription = applicationState.shipping?.selected_shipping?.description;
  const shippingLineErrors = state.errors.shippingLines;
  const memoizedShippingLines = useMemo(() => shippingLines, [JSON.stringify(shippingLines)]);
  const memoizedShippingLineErrors = useMemo(() => shippingLineErrors, [JSON.stringify(shippingLineErrors)]);

  const updateShippingLine = useCallback(async (index) => {
    dispatch({
      type: 'checkout/shippingLines/setting',
    });

    try {
      const response = await setShippingLine(token, apiPath, index);
      const error = handleError('shippingLines', response);
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

      if (response.data && response.data.application_state) {
        dispatch({
          type: 'checkout/shippingLines/set',
        });

        dispatch({
          type: 'checkout/update',
          payload: response.data.application_state,
        });

        return Promise.resolve(response);
      }
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

    dispatch({
      type: 'checkout/shippingLines/set',
    });

    return Promise.resolve();
  }, [onError]);

  const getShippingLines = useCallback(async () => {
    // Don't get shipping lines if shipping address is not set
    if (!selectedCountryCode) {
      return Promise.resolve();
    }

    dispatch({
      type: 'checkout/shippingLines/fetching',
    });
    try {
      const response = await fetchShippingLines(token, apiPath);
      const error = handleError('shippingLines', response);
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

      if (response.data && response.data.application_state) {
        dispatch({
          type: 'checkout/shippingLines/fetched',
        });

        dispatch({
          type: 'checkout/update',
          payload: response.data.application_state,
        });

        return Promise.resolve(response);
      }
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

    dispatch({
      type: 'checkout/shippingLines/fetched',
    });

    return Promise.resolve();
  }, [selectedCountryCode, onError]);

  return {
    data: {
      shippingLines: memoizedShippingLines,
      selectedShippingAmount,
      selectedShippingDescription,
      selectedShippingLineIndex,
    },
    errors: memoizedShippingLineErrors,
    loadingStatus: shippingLinesLoadingStatus,
    updateShippingLine,
    getShippingLines,
  };
};

export default useShippingLines;
