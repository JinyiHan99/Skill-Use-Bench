import { fetchApi } from '../utils';

export const deleteOrderMetadata = async (token, apiPath) => {
  const response = await fetchApi(`${apiPath}/meta_data`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  return response;
};

export const postOrderMetadata = async (token, apiPath, newOrderMetadata) => {
  const response = await fetchApi(`${apiPath}/meta_data`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(
      newOrderMetadata,
    ),
  });

  return response;
};

export const patchOrderMetadata = async (token, apiPath, requestBody) => {
  const response = await fetchApi(`${apiPath}/meta_data`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(
      requestBody,
    ),
  });

  return response;
};
