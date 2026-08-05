import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { createOpenApiDocument } from './openapi';

async function bootstrap(): Promise<void> {
  const { FastifyAdapter } = loadFastifyAdapter();
  const app = await NestFactory.create(
    AppModule,
    new FastifyAdapter() as never,
  );
  const document = createOpenApiDocument(app);

  SwaggerModule.setup('docs', app, document);

  await app.listen(3000, '0.0.0.0');
}

function loadFastifyAdapter(): { FastifyAdapter: new () => unknown } {
  try {
    return require('@nestjs/platform-fastify') as {
      FastifyAdapter: new () => unknown;
    };
  } catch (error) {
    if (isModuleNotFoundError(error)) {
      throw new Error(
        'Install @nestjs/platform-fastify in your application before running the Fastify showcase bootstrap.',
      );
    }

    throw error;
  }
}

function isModuleNotFoundError(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    (error as { code?: unknown }).code === 'MODULE_NOT_FOUND'
  );
}

void bootstrap();
