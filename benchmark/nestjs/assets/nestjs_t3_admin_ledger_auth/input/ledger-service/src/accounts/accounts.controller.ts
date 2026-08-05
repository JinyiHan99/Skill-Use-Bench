import {
  Body,
  Controller,
  Get,
  Post,
  UseGuards,
  UseInterceptors,
} from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { ApiKeyGuard } from '../common/api-key.guard';
import { RequestAuditInterceptor } from '../common/request-audit.interceptor';
import { AccountDto } from './account.dto';
import { AccountsService } from './accounts.service';
import { CreateAccountDto } from './create-account.dto';

@ApiTags('accounts')
@Controller('accounts')
@UseGuards(ApiKeyGuard)
@UseInterceptors(RequestAuditInterceptor)
export class AccountsController {
  constructor(private readonly accountsService: AccountsService) {}

  @Get()
  @ApiOkResponse({ type: AccountDto, isArray: true })
  list(): Promise<AccountDto[]> {
    return this.accountsService.list();
  }

  @Post()
  @ApiOkResponse({ type: AccountDto })
  create(@Body() body: CreateAccountDto): Promise<AccountDto> {
    return this.accountsService.create(body);
  }
}
