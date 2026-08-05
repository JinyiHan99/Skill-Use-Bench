import OrderError from './orderError';

const handleError = (actionType, response) => {
  if (!response.success) {
    if (response.error?.body?.errors && response.error.status !== 500) {
      if (response.error.status === 401) {
        return {
          type: 'order',
          payload: [{
            field: 'order',
            message: 'Your session has expired',
          }],
          error: response.error,
        };
      }
      return {
        type: actionType,
        payload: response.error.body.errors,
        error: response.error,
      };
    }

    return {
      type: 'order',
      payload: [{
        field: 'order',
        message: 'An error with your order has occured, please try again',
      }],
      error: new OrderError(),
    };
  }

  return null;
};

export default handleError;
