export default class PromiseError extends Error {
  constructor(message, body) {
    super(message);
    this.body = body;
  }
}
