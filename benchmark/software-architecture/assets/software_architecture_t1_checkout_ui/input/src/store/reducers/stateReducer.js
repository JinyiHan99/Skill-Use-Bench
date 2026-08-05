const stateReducer = (state, action) => {
  switch (action.type) {
    case 'checkout/update':
      return {
        ...state,
        ...action.payload,
      };
    default:
      return state;
  }
};

export default stateReducer;
