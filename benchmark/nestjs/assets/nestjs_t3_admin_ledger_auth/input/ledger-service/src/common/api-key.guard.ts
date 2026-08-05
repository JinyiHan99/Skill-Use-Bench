import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';

@Injectable()
export class ApiKeyGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest<{
      headers: Record<string, string | string[] | undefined>;
    }>();
    const apiKey = request.headers['x-api-key'];

    if (apiKey === 'showcase-secret') {
      return true;
    }

    throw new UnauthorizedException('Missing showcase API key');
  }
}
