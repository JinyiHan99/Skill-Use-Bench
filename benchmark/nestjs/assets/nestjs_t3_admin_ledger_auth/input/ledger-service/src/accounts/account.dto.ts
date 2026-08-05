import { ApiProperty } from '@nestjs/swagger';

export class AccountDto {
  @ApiProperty({ example: 1 })
  id!: number;

  @ApiProperty({ example: 'Ada Lovelace' })
  ownerName!: string;

  @ApiProperty({ example: 5000 })
  balanceCents!: number;
}
