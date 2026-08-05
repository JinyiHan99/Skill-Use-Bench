import fetchApi from '../utils/fetchApi';

export const validateShippingAddress = async (token, apiPath, address) => {
  const response = await fetchApi(`${apiPath}/validate_address?country_code=${address.country_code}&country=${address.country}&province_code=${address.province_code}&province=${address.province}&postal_code=${address.postal_code}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  return response;
};

export const updateShippingAddress = async (token, apiPath, address) => {
  const response = await fetchApi(`${apiPath}/addresses/shipping`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(address),
  });

  return response;
};
