import { useCallback, useContext, useMemo } from 'react';
import * as api from '../api';
import { CheckoutStore } from '../store';
import { handleError, OrderError } from '../utils';
import { getShippingLines } from './shared';

const useLineItems = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;
  const countryCode = state.applicationState.addresses?.shipping?.country_code;
  const lineItems = state.applicationState.line_items;
  const lineItemsLoadingStatus = state.loadingStatus.lineItems;
  const lineItemErrors = state.errors.lineItems;
  const memoizedLineItemErrors = useMemo(() => lineItemErrors, [JSON.stringify(lineItemErrors)]);
  const memoizedLineItems = useMemo(() => lineItems, [JSON.stringify(lineItems)]);

  const removeLineItem = useCallback(async (lineItemKey) => {
    dispatch({
      type: 'checkout/lineItem/removing',
    });

    try {
      const response = await api.removeLineItem(token, apiPath, lineItemKey);
      const error = handleError('lineItem', response);
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
        type: 'checkout/lineItem/removed',
      });

      dispatch({
        type: 'checkout/update',
        payload: response.data.application_state,
      });
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

    if (countryCode) {
      return getShippingLines(token, apiPath, dispatch);
    }
    return Promise.resolve();
  }, [countryCode, onError]);

  const updateLineItemQuantity = useCallback(async (lineItemKey, quantity) => {
    const data = {
      quantity,
      line_item_key: lineItemKey,
    };

    dispatch({
      type: 'checkout/lineItem/setting',
    });

    try {
      const response = await api.updateLineItem(token, apiPath, data);
      const error = handleError('lineItem', response);
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
        type: 'checkout/lineItem/set',
      });

      dispatch({
        type: 'checkout/update',
        payload: response.data.application_state,
      });
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

    if (countryCode) {
      return getShippingLines(token, apiPath, dispatch);
    }
    return Promise.resolve();
  }, [countryCode, onError]);

  const addLineItem = useCallback(async (platformId, lineItemKey, quantity) => {
    const data = {
      platform_id: platformId,
      quantity,
      line_item_key: lineItemKey,
    };

    dispatch({
      type: 'checkout/lineItem/adding',
    });

    try {
      const response = await api.addLineItem(token, apiPath, data);
      const error = handleError('lineItem', response);
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
        type: 'checkout/lineItem/added',
      });

      dispatch({
        type: 'checkout/update',
        payload: response.data.application_state,
      });
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

    if (countryCode) {
      return getShippingLines(token, apiPath, dispatch);
    }
    return Promise.resolve();
  }, [countryCode, onError]);

  return {
    data: memoizedLineItems,
    errors: memoizedLineItemErrors,
    loadingStatus: lineItemsLoadingStatus,
    addLineItem,
    updateLineItemQuantity,
    removeLineItem,
  };
};

export default useLineItems;
