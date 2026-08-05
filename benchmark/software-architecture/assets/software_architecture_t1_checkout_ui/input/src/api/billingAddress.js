import { fetchApi } from '../utils';

export const validateBillingAddress = async (token, apiPath, address) => {
  const response = await fetchApi(`${apiPath}/validate_address?country_code=${address.country_code}&province=${address.province}&postal_code=${address.postal_code}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  return response;
};

export const updateBillingAddress = async (token, apiPath, address) => {
  const response = await fetchApi(`${apiPath}/addresses/billing`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(address),
  });

  return response;
};

export const removeBillingAddress = async (token, apiPath) => {
  const response = await fetchApi(`${apiPath}/addresses/billing`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  return response;
};
