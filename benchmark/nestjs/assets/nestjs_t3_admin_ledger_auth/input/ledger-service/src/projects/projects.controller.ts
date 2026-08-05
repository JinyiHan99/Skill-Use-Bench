import { Body, Controller, Get, Post, UseGuards } from '@nestjs/common';
import { ApiOkResponse, ApiTags } from '@nestjs/swagger';
import { ApiKeyGuard } from '../common/api-key.guard';
import { CreateProjectDto } from './create-project.dto';
import { ProjectDto } from './project.dto';
import { ProjectsService } from './projects.service';

@ApiTags('projects')
@Controller('projects')
@UseGuards(ApiKeyGuard)
export class ProjectsController {
  constructor(private readonly projectsService: ProjectsService) {}

  @Get()
  @ApiOkResponse({ type: ProjectDto, isArray: true })
  list(): Promise<ProjectDto[]> {
    return this.projectsService.list();
  }

  @Post()
  @ApiOkResponse({ type: ProjectDto })
  create(@Body() body: CreateProjectDto): Promise<ProjectDto> {
    return this.projectsService.create(body);
  }
}
