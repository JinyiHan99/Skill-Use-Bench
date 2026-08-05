import { sql } from 'drizzle-orm';

import { tasks } from '../schemas/task';

export class TaskTreeRepository {
  constructor(private readonly db: any) {}

  async getSubtree(rootTaskId: string, userId: string) {
    const { rows } = await this.db.execute(sql`
      WITH RECURSIVE task_tree AS (
        SELECT id, parent_task_id
        FROM tasks
        WHERE id = ${rootTaskId} AND created_by_user_id = ${userId}
        UNION ALL
        SELECT t.id, t.parent_task_id
        FROM tasks t
        JOIN task_tree ON t.parent_task_id = task_tree.id
      )
      SELECT * FROM task_tree
    `);

    return rows;
  }
}
