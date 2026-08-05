import {
  useCallback, useContext, useMemo,
} from 'react';
import { CheckoutStore } from '../store';
import { updateCustomer } from '../api';
import { handleError, OrderError, PromiseError } from '../utils';

const emptyCustomer = {
  first_name: null,
  last_name: null,
  email_address: null,
};

const useCustomer = () => {
  const { state, dispatch, onError } = useContext(CheckoutStore);
  const { token, apiPath } = state;
  const { customer } = state.applicationState;
  const customerLoadingStatus = state.loadingStatus.customer;
  const customerErrors = state.errors.customer;
  const { isAuthenticated } = state;
  const emailAddress = customer?.email_address;
  const firstName = customer?.first_name;
  const lastName = customer?.last_name;
  const memoizedCustomer = useMemo(() => ({
    ...customer,
    isAuthenticated,
  }), [emailAddress, firstName, lastName, isAuthenticated]);
  const memoizedCustomerErrors = useMemo(() => customerErrors, [JSON.stringify(customerErrors)]);

  const submitCustomer = useCallback(async (customerData) => {
    if (!customerData.email_address) {
      dispatch({
        type: 'checkout/customer/setErrors',
        payload: [{
          field: 'email',
          message: 'Email address is required',
        }],
      });
      return Promise.reject(new PromiseError('Email address is required', {
        errors: [
          {
            field: 'email',
            message: 'Email address is required',
          },
        ],
      }));
    }

    const appCustomer = JSON.stringify({
      first_name: memoizedCustomer.first_name,
      last_name: memoizedCustomer.last_name,
      email_address: memoizedCustomer.email_address,
    });
    const localCustomer = JSON.stringify({
      ...emptyCustomer,
      ...customerData,
    });

    // Prevent customer from being resubmitted with same data
    if (appCustomer === localCustomer) {
      return Promise.resolve();
    }

    const method = memoizedCustomer.email_address ? 'PUT' : 'POST';
    try {
      const response = await updateCustomer(token, apiPath, customerData, method);
      const error = handleError('customer', response);
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
        type: 'checkout/customer/set',
        payload: response.data.customer,
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
  }, [memoizedCustomer, token, apiPath, onError]);

  return {
    data: memoizedCustomer,
    errors: memoizedCustomerErrors,
    loadingStatus: customerLoadingStatus,
    submitCustomer,
  };
};

export default useCustomer;
