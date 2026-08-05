import { ApiProperty } from '@nestjs/swagger';
import { IsInt, IsString, Min, MinLength } from 'class-validator';

export class CreateAccountDto {
  @ApiProperty({ example: 'Ada Lovelace' })
  @IsString()
  @MinLength(2)
  ownerName!: string;

  @ApiProperty({ example: 5000, minimum: 0 })
  @IsInt()
  @Min(0)
  balanceCents!: number;
}
