const orderInfoReducer = (state, action) => {
  switch (action.type) {
    case 'checkout/billingAddress/setBillingSameAsShipping':
      return {
        ...state,
        billingSameAsShipping: action.payload,
      };
    case 'checkout/order/processing':
      return {
        ...state,
        orderStatus: 'processing',
      };
    case 'checkout/paymentIframe/authorizing':
      return {
        ...state,
        orderStatus: 'authorizing',
      };
    case 'checkout/paymentIframe/setPaymentIframeErrors':
      return {
        ...state,
        orderStatus: 'error',
      };
    case 'checkout/order/setErrors':
      return {
        ...state,
        orderStatus: 'error',
      };
    case 'checkout/order/processed':
      return {
        ...state,
        orderStatus: 'completed',
      };
    default:
      return state;
  }
};

export default orderInfoReducer;
