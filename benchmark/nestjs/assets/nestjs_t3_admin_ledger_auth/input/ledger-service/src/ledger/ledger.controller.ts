import { Controller, Get, UseGuards } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { ApiKeyGuard } from '../common/api-key.guard';
import { LedgerEntryDto } from './ledger-entry.dto';
import { LedgerService } from './ledger.service';

@ApiTags('ledger')
@Controller('ledger')
@UseGuards(ApiKeyGuard)
export class LedgerController {
  constructor(private readonly ledgerService: LedgerService) {}

  @Get()
  @ApiOkResponse({ type: LedgerEntryDto, isArray: true })
  list(): Promise<LedgerEntryDto[]> {
    return this.ledgerService.list();
  }
}
