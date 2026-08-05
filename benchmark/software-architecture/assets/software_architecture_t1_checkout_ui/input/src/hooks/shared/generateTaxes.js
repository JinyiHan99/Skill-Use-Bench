import { fetchTaxes } from '../../api';
import { handleError } from '../../utils';

const generateTaxes = async (token, apiPath, dispatch) => {
  const response = await fetchTaxes(token, apiPath);
  const error = handleError('taxes', response);
  if (error) {
    dispatch({
      type: `checkout/${error.type}/setErrors`,
      payload: error.payload,
    });

    return Promise.reject(error.error);
  }

  if (response.data && response.data.application_state) {
    dispatch({
      type: 'checkout/update',
      payload: response.data.application_state,
    });

    return Promise.resolve(response);
  }
  return Promise.resolve();
};

export default generateTaxes;
