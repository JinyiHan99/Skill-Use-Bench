import { asc, eq } from 'drizzle-orm';

import {
  agentEvalRunTopics,
  agentEvalRuns,
} from '../schemas/agentEvals';

export class AgentEvalRepository {
  constructor(private readonly db: any) {}

  async getRun(id: string) {
    return this.db.query.agentEvalRuns.findFirst({
      where: eq(agentEvalRuns.id, id),
      with: {
        dataset: true,
      },
    });
  }

  async listRunTopics(runId: string) {
    return this.db.query.agentEvalRunTopics.findMany({
      where: eq(agentEvalRunTopics.runId, runId),
      with: {
        testCase: true,
        topic: true,
      },
      orderBy: asc(agentEvalRunTopics.createdAt),
    });
  }
}
