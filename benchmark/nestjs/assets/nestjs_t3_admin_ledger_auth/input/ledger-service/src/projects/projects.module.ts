import { Module } from '@nestjs/common';
import { DrizzleModule } from '@nest-native/drizzle';
import { ProjectsController } from './projects.controller';
import { ProjectsRepository } from './projects.repository';
import { ProjectsService } from './projects.service';

@Module({
  imports: [DrizzleModule.forFeature([ProjectsRepository])],
  controllers: [ProjectsController],
  providers: [ProjectsService],
  exports: [DrizzleModule, ProjectsService],
})
export class ProjectsModule {}
