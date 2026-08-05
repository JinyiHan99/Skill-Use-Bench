import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsBoolean, IsInt, IsOptional, Min } from 'class-validator';

export class TransferDto {
  @ApiProperty({ example: 1 })
  @IsInt()
  @Min(1)
  fromAccountId!: number;

  @ApiProperty({ example: 2 })
  @IsInt()
  @Min(1)
  toAccountId!: number;

  @ApiProperty({ example: 1250, minimum: 1 })
  @IsInt()
  @Min(1)
  amountCents!: number;

  @ApiPropertyOptional({ example: false })
  @IsOptional()
  @IsBoolean()
  fail?: boolean;
}

export class TransferResultDto {
  @ApiProperty({ example: true })
  transactionActive!: boolean;

  @ApiProperty({ example: 'req-showcase-1' })
  requestId!: string;
}
