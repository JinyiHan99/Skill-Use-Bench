import {
  BadRequestException,
  Injectable,
  PipeTransform,
} from '@nestjs/common';
import { type ZodType } from 'zod';

@Injectable()
export class ZodValidationPipe<TInput = unknown, TOutput = unknown>
  implements PipeTransform<TInput, TOutput>
{
  constructor(private readonly schema: ZodType<TOutput, TInput>) {}

  transform(value: TInput): TOutput {
    const result = this.schema.safeParse(value);

    if (!result.success) {
      throw new BadRequestException({
        message: 'Validation failed',
        issues: result.error.issues,
      });
    }

    return result.data;
  }
}
