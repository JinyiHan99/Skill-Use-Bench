import { useContext, useCallback, useMemo } from 'react';
import { CheckoutStore } from '../store';
import { runAppHook } from '../api';
import { handleError, OrderError } from '../utils';

const useAppHook = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;

  const appHookErrors = state.errors.appHook;
  const appHookLoadingStatus = state.loadingStatus.appHook;
  const memoizedAppHookErrors = useMemo(
    () => appHookErrors,
    [JSON.stringify(appHookErrors)],
  );

  const invokeAppHook = useCallback(
    async (hook, uuid, data) => {
      try {
        dispatch({
          type: 'checkout/appHook/setting',
        });
        const response = await runAppHook(token, apiPath, hook, uuid, data);
        const error = handleError('appHook', response);
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
          type: 'checkout/appHook/set',
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
          type: 'checkout/appHook/setErrors',
          payload: [
            {
              field: 'appHook',
              message: 'An error with your order has occured, please try again',
            },
          ],
        });

        return Promise.reject(new OrderError());
      }
    },
    [token, apiPath],
  );

  return {
    errors: memoizedAppHookErrors,
    loadingStatus: appHookLoadingStatus,
    invokeAppHook,
  };
};

export default useAppHook;
