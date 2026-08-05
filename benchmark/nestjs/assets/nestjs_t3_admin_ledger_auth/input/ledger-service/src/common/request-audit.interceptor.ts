import {
  CallHandler,
  ExecutionContext,
  Injectable,
  NestInterceptor,
} from '@nestjs/common';
import { Observable, tap } from 'rxjs';

@Injectable()
export class RequestAuditInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const response = context.switchToHttp().getResponse<{
      setHeader?: (name: string, value: string) => void;
      header?: (name: string, value: string) => void;
    }>();

    response.setHeader?.('x-showcase-enhancer', 'interceptor');
    response.header?.('x-showcase-enhancer', 'interceptor');

    return next.handle().pipe(tap(() => undefined));
  }
}
