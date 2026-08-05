import { Injectable } from '@nestjs/common';
import {
  ProjectsRepository,
  type Project,
} from './projects.repository';

@Injectable()
export class ProjectsService {
  constructor(private readonly projectsRepository: ProjectsRepository) {}

  list(): Promise<Project[]> {
    return this.projectsRepository.list();
  }

  create(input: { name: string; status: string }): Promise<Project> {
    return this.projectsRepository.create(input);
  }
}
