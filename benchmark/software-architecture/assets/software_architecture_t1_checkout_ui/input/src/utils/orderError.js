export default class PromiseError extends Error {
  constructor() {
    super('Something went wrong');
    this.body = {
      errors: [
        {
          field: 'order',
          message: 'An error with your order has occured, please try again',
        },
      ],
    };
  }
}
