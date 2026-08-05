import { ApiProperty } from '@nestjs/swagger';
import { IsIn, IsString, MinLength } from 'class-validator';

export class CreateProjectDto {
  @ApiProperty({ example: 'Publish showcase docs' })
  @IsString()
  @MinLength(3)
  name!: string;

  @ApiProperty({ enum: ['planned', 'active', 'done'], example: 'active' })
  @IsString()
  @IsIn(['planned', 'active', 'done'])
  status!: string;
}
