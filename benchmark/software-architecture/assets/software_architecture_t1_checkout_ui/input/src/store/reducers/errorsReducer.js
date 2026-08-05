const errorsReducer = (state, action) => {
  switch (action.type) {
    // App Hook Actions
    case 'checkout/appHook/setErrors':
      return {
        ...state,
        appHook: action.payload,
      };
    case 'checkout/appHook/set':
      return {
        ...state,
        appHook: null,
      };

    // Customer Actions
    case 'checkout/customer/setErrors':
      return {
        ...state,
        customer: action.payload,
      };
    case 'checkout/customer/set':
      return {
        ...state,
        customer: null,
        order: null,
      };

    // Shipping Address Actions
    case 'checkout/shippingAddress/setErrors':
      return {
        ...state,
        shippingAddress: action.payload,
      };
    case 'checkout/shippingAddress/set':
      return {
        ...state,
        shippingAddress: null,
        order: null,
      };

    // Billing Address Actions
    case 'checkout/billingAddress/setErrors':
      return {
        ...state,
        billingAddress: action.payload,
      };
    case 'checkout/billingAddress/set':
      return {
        ...state,
        billingAddress: null,
        order: null,
      };

    // Shipping Line Actions
    case 'checkout/shippingLines/setErrors':
      return {
        ...state,
        shippingLines: action.payload,
      };
    case 'checkout/shippingLines/set':
      return {
        ...state,
        shippingLines: null,
        order: null,
      };

    // Line Item Actions
    case 'checkout/lineItem/setErrors':
      return {
        ...state,
        lineItems: action.payload,
      };
    case 'checkout/lineItem/set':
      return {
        ...state,
        lineItems: null,
        order: null,
      };

    // Payment Iframe Actions
    case 'checkout/paymentIframe/setPaymentIframeErrors':
      return {
        ...state,
        paymentIframe: action.payload,
      };

    // Order Actions
    case 'checkout/order/setErrors':
      return {
        ...state,
        order: action.payload,
      };
    case 'checkout/order/clearErrors':
      return {
        ...state,
        order: null,
      };
    case 'checkout/order/set':
      return {
        ...state,
        order: null,
      };
    case 'checkout/order/processing':
      return {
        ...state,
        order: null,
      };

    // Discount Actions
    case 'checkout/discount/setErrors':
      return {
        ...state,
        discount: action.payload,
      };
    case 'checkout/discount/added':
      return {
        ...state,
        discount: null,
        order: null,
      };
    case 'checkout/discount/removed':
      return {
        ...state,
        discount: null,
        order: null,
      };

    // Order Metadata Actions
    case 'checkout/orderMetadata/setErrors':
      return {
        ...state,
        orderMetadata: action.payload,
      };
    case 'checkout/orderMetadata/set':
      return {
        ...state,
        orderMetadata: null,
        order: null,
      };

    default:
      return state;
  }
};

export default errorsReducer;
