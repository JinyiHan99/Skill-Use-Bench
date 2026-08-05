/* eslint-disable react/forbid-prop-types */
import React, { useReducer } from 'react';
import PropTypes from 'prop-types';
import {
  initialState, reducer, CheckoutStore, calculateTotals,
} from '../../store';

const CheckoutProvider = ({
  applicationState,
  initialData,
  publicOrderId,
  token,
  storeIdentifier,
  children,
  apiBase = 'https://api.boldcommerce.com/checkout/storefront',
  onError,
}) => {
  const apiPath = `${apiBase}/${storeIdentifier}/${publicOrderId}`;
  const orderTotals = calculateTotals(applicationState);
  const currentState = {
    ...initialState,
    applicationState,
    initialData,
    isAuthenticated: applicationState?.customer?.platform_id && true,
    publicOrderId,
    token,
    storeIdentifier,
    apiBase,
    apiPath,
    orderTotals,
    orderInfo: {
      ...initialState.orderInfo,
      orderStatus: orderTotals.remainingBalance === 0 ? 'completed' : 'pending',
    },
  };

  const [state, dispatch] = useReducer(reducer, currentState);

  return (
    <CheckoutStore.Provider value={{ state, dispatch, onError }}>
      {children}
    </CheckoutStore.Provider>
  );
};

CheckoutProvider.propTypes = {
  applicationState: PropTypes.any.isRequired,
  initialData: PropTypes.any.isRequired,
  publicOrderId: PropTypes.string.isRequired,
  token: PropTypes.string.isRequired,
  storeIdentifier: PropTypes.string.isRequired,
  apiBase: PropTypes.string,
  children: PropTypes.node,
  onError: PropTypes.func,
};

export default CheckoutProvider;
