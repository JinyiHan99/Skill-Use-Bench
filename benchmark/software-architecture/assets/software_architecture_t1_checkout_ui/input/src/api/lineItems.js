import { fetchApi } from '../utils';

export const addLineItem = async (token, apiPath, data) => {
  const response = await fetchApi(`${apiPath}/items`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  return response;
};

export const updateLineItem = async (token, apiPath, data) => {
  const response = await fetchApi(`${apiPath}/items`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  return response;
};

export const removeLineItem = async (token, apiPath, lineItemKey) => {
  const response = await fetchApi(`${apiPath}/items`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      quantity: 0,
      line_item_key: lineItemKey,
    }),
  });

  return response;
};
