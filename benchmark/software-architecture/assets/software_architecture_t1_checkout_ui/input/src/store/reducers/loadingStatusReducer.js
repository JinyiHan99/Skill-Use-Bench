const setLoadingState = (state, type, status) => {
  const loadingState = {
    ...state,
    [type]: status,
  };

  const isLoading = Object.values(loadingState).some((value) => value === 'fetching' || value === 'setting');

  return {
    ...loadingState,
    isLoading,
  };
};

const clearLoadingState = () => ({
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
});

const loadingStatusReducer = (state, action) => {
  switch (action.type) {
    // App Hook Actions
    case 'checkout/appHook/setting':
      return setLoadingState(state, 'appHook', 'setting');
    case 'checkout/appHook/set':
      return setLoadingState(state, 'appHook', 'fulfilled');
    case 'checkout/appHook/setErrors':
      return setLoadingState(state, 'appHook', 'fulfilled');

    // Customer Actions
    case 'checkout/customer/setting':
      return setLoadingState(state, 'customer', 'setting');
    case 'checkout/customer/set':
      return setLoadingState(state, 'customer', 'fulfilled');
    case 'checkout/customer/setErrors':
      return setLoadingState(state, 'customer', 'fulfilled');

    // Shipping Address Actions
    case 'checkout/shippingAddress/setIncomplete':
      return setLoadingState(state, 'shippingAddress', 'incomplete');
    case 'checkout/shippingAddress/setting':
      return setLoadingState(state, 'shippingAddress', 'setting');
    case 'checkout/shippingAddress/set':
      return setLoadingState(state, 'shippingAddress', 'fulfilled');
    case 'checkout/shippingAddress/setErrors':
      return setLoadingState(state, 'shippingAddress', 'fulfilled');

    // Billing Address Actions
    case 'checkout/billingAddress/setIncomplete':
      return setLoadingState(state, 'billingAddress', 'incomplete');
    case 'checkout/billingAddress/setting':
      return setLoadingState(state, 'billingAddress', 'setting');
    case 'checkout/billingAddress/set':
      return setLoadingState(state, 'billingAddress', 'fulfilled');
    case 'checkout/billingAddress/setErrors':
      return setLoadingState(state, 'billingAddress', 'fulfilled');

    // Shipping Line Actions
    case 'checkout/shippingLines/fetching':
      return setLoadingState(state, 'shippingLines', 'fetching');
    case 'checkout/shippingLines/fetched':
      return setLoadingState(state, 'shippingLines', 'fulfilled');
    case 'checkout/shippingLines/setting':
      return setLoadingState(state, 'shippingLines', 'setting');
    case 'checkout/shippingLines/set':
      return setLoadingState(state, 'shippingLines', 'fulfilled');

    // Payment Iframe Actions
    case 'checkout/paymentIframe/fetching':
      return setLoadingState(state, 'paymentIframe', 'fetching');
    case 'checkout/paymentIframe/fetched':
      return setLoadingState(state, 'paymentIframe', 'fulfilled');
    case 'checkout/paymentIframe/authorizing':
      return setLoadingState(state, 'paymentIframe', 'setting');
    case 'checkout/paymentIframe/setPaymentIframeErrors':
      return setLoadingState(state, 'paymentIframe', 'fulfilled');

    // Order Actions
    case 'checkout/order/setErrors':
      return clearLoadingState();

    // Line Item Actions
    case 'checkout/lineItem/removing':
      return setLoadingState(state, 'lineItems', 'setting');
    case 'checkout/lineItem/removed':
      return setLoadingState(state, 'lineItems', 'fulfilled');
    case 'checkout/lineItem/setting':
      return setLoadingState(state, 'lineItems', 'setting');
    case 'checkout/lineItem/set':
      return setLoadingState(state, 'lineItems', 'fulfilled');
    case 'checkout/lineItem/adding':
      return setLoadingState(state, 'lineItems', 'setting');
    case 'checkout/lineItem/added':
      return setLoadingState(state, 'lineItems', 'fulfilled');

    // Discount Actions
    case 'checkout/discount/adding':
      return setLoadingState(state, 'discount', 'setting');
    case 'checkout/discount/added':
      return setLoadingState(state, 'discount', 'fulfilled');
    case 'checkout/discount/removing':
      return setLoadingState(state, 'discount', 'setting');
    case 'checkout/discount/removed':
      return setLoadingState(state, 'discount', 'fulfilled');
    case 'checkout/discount/setErrors':
      return setLoadingState(state, 'discount', 'fulfilled');

    // Order Metadata Actions
    case 'checkout/orderMetadata/setting':
      return setLoadingState(state, 'orderMetadata', 'setting');
    case 'checkout/orderMetadata/set':
      return setLoadingState(state, 'orderMetadata', 'fulfilled');

    default:
      return state;
  }
};

export default loadingStatusReducer;
