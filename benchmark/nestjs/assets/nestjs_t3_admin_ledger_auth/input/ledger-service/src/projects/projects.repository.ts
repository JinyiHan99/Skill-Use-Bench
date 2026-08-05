import { desc, sql } from 'drizzle-orm';
import { DrizzleRepository, InjectDrizzle } from '@nest-native/drizzle';
import type { AppDatabase } from '../database';
import { projects } from '../schema';

export type Project = typeof projects.$inferSelect;

@DrizzleRepository()
export class ProjectsRepository {
  constructor(@InjectDrizzle() private readonly db: AppDatabase) {}

  async migrate(): Promise<void> {
    await this.db.run(sql`
      CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
      )
    `);
    await this.db.delete(projects);
  }

  async seed(): Promise<void> {
    await this.create({
      name: 'Complete the Nest-native Drizzle showcase',
      status: 'active',
    });
  }

  async list(): Promise<Project[]> {
    return this.db.select().from(projects).orderBy(desc(projects.id));
  }

  async create(input: {
    name: string;
    status: string;
  }): Promise<Project> {
    const [project] = await this.db
      .insert(projects)
      .values({
        ...input,
        createdAt: new Date().toISOString(),
      })
      .returning();

    return project;
  }
}
