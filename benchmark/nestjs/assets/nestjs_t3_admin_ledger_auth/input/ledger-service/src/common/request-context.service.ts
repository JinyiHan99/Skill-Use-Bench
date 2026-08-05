import { Inject, Injectable, Scope } from '@nestjs/common';
import { REQUEST } from '@nestjs/core';

type RequestLike = {
  headers?: Record<string, string | string[] | undefined>;
};

@Injectable({ scope: Scope.REQUEST })
export class RequestContextService {
  constructor(@Inject(REQUEST) private readonly request: RequestLike) {}

  requestId(): string {
    const header = this.request.headers?.['x-request-id'];

    if (Array.isArray(header)) {
      return header[0] ?? 'missing-request-id';
    }

    return header ?? 'missing-request-id';
  }
}
