import { ApiProperty } from '@nestjs/swagger';

export class LedgerEntryDto {
  @ApiProperty({ example: 1 })
  id!: number;

  @ApiProperty({ example: 1 })
  fromAccountId!: number;

  @ApiProperty({ example: 2 })
  toAccountId!: number;

  @ApiProperty({ example: 1250 })
  amountCents!: number;

  @ApiProperty({ example: 'req-showcase-1' })
  requestId!: string;

  @ApiProperty({ example: 'committed transfer' })
  note!: string;
}
