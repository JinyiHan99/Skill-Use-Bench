import fetchApi from '../utils/fetchApi';

const runAppHook = async (token, apiPath, hook, uuid, data) => {
  const response = await fetchApi(`${apiPath}/app_hook`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      hook,
      uuid,
      app_hook_data: data,
    }),
  });

  return response;
};

export default runAppHook;
