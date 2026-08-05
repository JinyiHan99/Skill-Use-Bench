import React from 'react';

export const initialState = {
  applicationState: {},
  initialData: {},
  publicOrderId: null,
  token: null,
  storeIdentifier: null,
  apiBase: 'https://api.boldcommerce.com/checkout/storefront',
  apiPath: '',
  isAuthenticated: false,
  orderInfo: {
    orderStatus: 'pending',
    billingSameAsShipping: true,
  },
  orderTotals: {
    subTotal: 0,
    shippingTotal: 0,
    excludedTaxes: 0,
    discountTotal: 0,
    total: 0,
    remainingBalance: 0,
    taxesTotal: 0,
    totalItems: 0,
  },
  errors: {
    appHook: null,
    customer: null,
    shippingAddress: null,
    billingAddress: null,
    shippingLines: null,
    lineItems: null,
    orderMetadata: null,
    discount: null,
    paymentIframe: null,
    order: null,
  },
  loadingStatus: {
    appHook: 'fulfilled',
    customer: 'fulfilled',
    shippingAddress: 'fulfilled',
    billingAddress: 'fulfilled',
    shippingLines: 'fulfilled',
    paymentIframe: 'fulfilled',
    lineItems: 'fulfilled',
    discount: 'fulfilled',
    orderMetadata: 'fulfilled',
    isLoading: false,
  },
};

export const CheckoutStore = React.createContext(null);
