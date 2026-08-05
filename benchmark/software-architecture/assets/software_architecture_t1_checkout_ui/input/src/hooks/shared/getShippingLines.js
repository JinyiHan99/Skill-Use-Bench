import { fetchShippingLines } from '../../api';
import { handleError } from '../../utils';

const getShippingLines = async (token, apiPath, dispatch) => {
  dispatch({
    type: 'checkout/shippingLines/fetching',
  });
  const response = await fetchShippingLines(token, apiPath);
  const error = handleError('shippingLines', response);
  if (error) {
    dispatch({
      type: `checkout/${error.type}/setErrors`,
      payload: error.payload,
    });

    return Promise.reject(error.error);
  }

  if (response.data && response.data.application_state) {
    dispatch({
      type: 'checkout/shippingLines/fetched',
    });
    dispatch({
      type: 'checkout/update',
      payload: response.data.application_state,
    });

    return Promise.resolve(response);
  }

  dispatch({
    type: 'checkout/shippingLines/fetched',
  });

  return Promise.resolve();
};

export default getShippingLines;
