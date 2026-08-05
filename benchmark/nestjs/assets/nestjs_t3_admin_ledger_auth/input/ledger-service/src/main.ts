import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';
import { SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';
import { createOpenApiDocument } from './openapi';

/**
 * Bootstrap the showcase and serve the generated OpenAPI document via Swagger.
 *
 * The HTTP driver is passed explicitly via `ExpressAdapter` rather than relying
 * on `NestFactory`'s default-driver auto-discovery. Auto-discovery resolves
 * `@nestjs/platform-express` relative to `@nestjs/core`'s install location, so
 * it only works when both are hoisted together — a fragile assumption in a
 * workspace where a lockfile refresh can nest `platform-express` under this
 * sample. Constructing the adapter here resolves it from the showcase's own
 * dependency (declared in this package), independent of hoisting.
 */
async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, new ExpressAdapter());
  const document = createOpenApiDocument(app);

  SwaggerModule.setup('docs', app, document);

  await app.listen(3000);
}

void bootstrap();
