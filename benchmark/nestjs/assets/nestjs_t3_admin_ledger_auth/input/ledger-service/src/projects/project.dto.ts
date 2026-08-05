import { ApiProperty } from '@nestjs/swagger';

export class ProjectDto {
  @ApiProperty({ example: 1 })
  id!: number;

  @ApiProperty({ example: 'Publish showcase docs' })
  name!: string;

  @ApiProperty({ example: 'active' })
  status!: string;

  @ApiProperty({ example: '2026-05-07T00:00:00.000Z' })
  createdAt!: string;
}
