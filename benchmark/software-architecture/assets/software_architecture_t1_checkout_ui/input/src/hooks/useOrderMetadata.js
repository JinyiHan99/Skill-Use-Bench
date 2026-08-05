import { useContext, useCallback, useMemo } from 'react';
import { CheckoutStore } from '../store';
import { deleteOrderMetadata, postOrderMetadata, patchOrderMetadata } from '../api';
import { handleError, OrderError } from '../utils';

const useOrderMetadata = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;
  const orderMetadata = state.applicationState.order_meta_data;
  const orderMetadataLoadingStatus = state.loadingStatus.orderMetadata;
  const orderMetadataErrors = state.errors.orderMetadata;
  const memoizedOrderMetadata = useMemo(() => orderMetadata, [JSON.stringify(orderMetadata)]);
  const memoizedOrderMetadataErrors = useMemo(() => orderMetadataErrors, [JSON.stringify(orderMetadataErrors)]);

  const clearOrderMetadata = useCallback(async () => {
    try {
      dispatch({
        type: 'checkout/orderMetadata/setting',
      });
      const response = await deleteOrderMetadata(token, apiPath);
      const error = handleError('orderMetadata', response);
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
        type: 'checkout/orderMetadata/set',
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
  }, [token, apiPath]);

  const overwriteOrderMetadata = useCallback(async (newOrderMetadata) => {
    try {
      dispatch({
        type: 'checkout/orderMetadata/setting',
      });
      const response = await postOrderMetadata(token, apiPath, newOrderMetadata);
      const error = handleError('orderMetadata', response);
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
        type: 'checkout/orderMetadata/set',
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
  }, [token, apiPath]);

  const appendOrderMetadata = useCallback(async (data) => {
    try {
      dispatch({
        type: 'checkout/orderMetadata/setting',
      });
      const response = await patchOrderMetadata(token, apiPath, data);
      const error = handleError('orderMetadata', response);
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
        type: 'checkout/orderMetadata/set',
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
  }, [token, apiPath]);

  return {
    data: memoizedOrderMetadata,
    errors: memoizedOrderMetadataErrors,
    loadingStatus: orderMetadataLoadingStatus,
    appendOrderMetadata,
    overwriteOrderMetadata,
    clearOrderMetadata,
  };
};

export default useOrderMetadata;
