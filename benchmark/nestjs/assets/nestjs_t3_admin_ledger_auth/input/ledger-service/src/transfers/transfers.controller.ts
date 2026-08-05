import {
  Body,
  Controller,
  Post,
  UseFilters,
  UseGuards,
  UsePipes,
} from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { ApiKeyGuard } from '../common/api-key.guard';
import { DomainErrorFilter } from '../common/domain-error.filter';
import { ZodValidationPipe } from '../common/zod-validation.pipe';
import { TransferDto, TransferResultDto } from './transfer.dto';
import { TransfersService } from './transfers.service';
import {
  transferSchema,
  type TransferInput,
} from './transfer.validation';

@ApiTags('transfers')
@Controller('transfers')
@UseGuards(ApiKeyGuard)
@UseFilters(DomainErrorFilter)
export class TransfersController {
  constructor(private readonly transfersService: TransfersService) {}

  @Post()
  @UsePipes(new ZodValidationPipe(transferSchema))
  @ApiOkResponse({ type: TransferResultDto })
  transfer(@Body() body: TransferDto): Promise<TransferResultDto> {
    return this.transfersService.transfer(body as TransferInput);
  }
}
