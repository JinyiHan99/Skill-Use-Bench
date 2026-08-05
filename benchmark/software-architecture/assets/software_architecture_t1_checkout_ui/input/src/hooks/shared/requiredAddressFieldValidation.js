const requiredAddressFieldValidation = (currAddress, requiredAddressFields) => {
  const foundErrors = requiredAddressFields.reduce((result, requiredField) => {
    if (!currAddress[requiredField]) {
      result.push({
        field: requiredField,
        message: 'This field is required',
      });
    }
    return result;
  }, []);

  return foundErrors.length ? foundErrors : null;
};

export default requiredAddressFieldValidation;
