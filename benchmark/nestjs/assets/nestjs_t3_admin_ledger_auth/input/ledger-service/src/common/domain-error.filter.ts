import {
  ArgumentsHost,
  Catch,
  ConflictException,
  ExceptionFilter,
} from '@nestjs/common';

export class DomainError extends Error {}

@Catch(DomainError)
export class DomainErrorFilter implements ExceptionFilter<DomainError> {
  catch(error: DomainError, host: ArgumentsHost): void {
    const response = host.switchToHttp().getResponse<{
      status: (code: number) => {
        json?: (body: unknown) => void;
        send?: (body: unknown) => void;
      };
    }>();
    const exception = new ConflictException(error.message);
    const reply = response.status(exception.getStatus());
    const body = exception.getResponse();

    if (reply.json) {
      reply.json(body);
      return;
    }

    reply.send?.(body);
  }
}
