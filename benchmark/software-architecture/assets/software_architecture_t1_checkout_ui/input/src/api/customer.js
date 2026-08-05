import fetchApi from '../utils/fetchApi';

export const validateCustomer = async (token, apiPath, customer) => {
  const email = encodeURIComponent(customer.email_address);

  const response = await fetchApi(`${apiPath}/validate_email_address?email_address=${email}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  return response;
};

export const updateCustomer = async (token, apiPath, customer, method) => {
  const response = await fetchApi(`${apiPath}/customer/guest`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(customer),
  });

  return response;
};
