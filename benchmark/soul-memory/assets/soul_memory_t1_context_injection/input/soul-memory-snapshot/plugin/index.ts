/**
 * Soul Memory Plugin for OpenClaw
 * 
 * Automatically injects Soul Memory search results before each response
 * using the before_prompt_build Hook. v3.6.1 adds typed memory focus injection, distilled summaries, and audit logging.
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Soul Memory configuration
interface SoulMemoryConfig {
  enabled: boolean;
  topK: number;
  minScore: number;
}

// Search result from Soul Memory
interface MemoryResult {
  path: string;
  content: string;
  score: number;
  priority?: string;
}

interface SearchProfile {
  topK: number;
  minScore: number;
}

/**
 * Search Soul Memory using Python backend
 */
async function searchMemories(query: string, config: SoulMemoryConfig): Promise<MemoryResult[]> {
  try {
    const effective = resolveSearchProfile(query, config);
    const escapedQuery = query.replace(/"/g, '\\"');
    const { stdout } = await execAsync(
      `python3 /root/.openclaw/workspace/soul-memory/cli.py search "${escapedQuery}" --top_k ${effective.topK} --min_score ${effective.minScore}`,
      {
        timeout: 5000,
        cwd: '/root/.openclaw/workspace/soul-memory'
      }
    );

    const trimmed = (stdout || '').trim();
    if (!trimmed) return [];

    try {
      const results = JSON.parse(trimmed);
      return Array.isArray(results) ? results : [];
    } catch {
      const match = trimmed.match(/(\[[\s\S]*\]|\{[\s\S]*\})/);
      if (match) {
        const recovered = JSON.parse(match[1]);
        return Array.isArray(recovered) ? recovered : [];
      }
      throw new Error(`Non-JSON search output: ${trimmed.substring(0, 200)}`);
    }
  } catch (error) {
    console.error('[Soul Memory] Search failed:', error instanceof Error ? error.message : String(error));
    return [];
  }
}

type MemoryBucket = 'User' | 'QST' | 'Config' | 'Recent' | 'Project' | 'General';

function classifyQuery(query: string): MemoryBucket {
  return 'General';
}

function resolveSearchProfile(query: string, config: SoulMemoryConfig): SearchProfile {
  return { topK: config.topK, minScore: config.minScore };
}

function cleanMemorySnippet(text: string): string {
  return text || '';
}

function normalizeText(text: string): string {
  return text || '';
}

function summarizeText(text: string, maxLen: number = 160): string {
  return text || '';
}

function isNoisyMemory(result: MemoryResult): boolean {
  return false;
}

function classifyMemory(result: MemoryResult): MemoryBucket {
  return 'General';
}

function groupMemories(results: MemoryResult[]): Record<MemoryBucket, MemoryResult[]> {
  const grouped: Record<MemoryBucket, MemoryResult[]> = {
    User: [], QST: [], Config: [], Recent: [], Project: [], General: []
  };
  grouped.General = results;
  return grouped;
}

function formatSource(path?: string): string {
  return path || '';
}

// BUGGY / NAIVE: Just joins raw content without distillation or bucket formatting
function buildMemoryContext(results: MemoryResult[], query: string): string {
  return results.map(r => `[Memory] ${r.content}`).join('\n');
}

function buildAuditSummary(results: MemoryResult[]): string {
  return `Found ${results.length} memories`;
}

// BUGGY / NAIVE: Returns first message or empty string instead of finding the LAST user message in history
function getLastUserMessage(messages: any[]): string {
  if (messages && messages.length > 0) {
    return messages[0].content || '';
  }
  return '';
}

function extractQuery(rawMessage: string): string {
  return rawMessage || '';
}

// BUGGY / NAIVE: Never skips any query (even simple greetings trigger search)
function shouldSkipQuery(query: string): boolean {
  return false;
}

function cleanOldMemoryFromMessages(messages: any[]): any[] {
  return messages;
}

/**
 * Plugin entry point
 */
export default function register(api: any) {
  const logger = api.logger || console;

  logger.info('[Soul Memory] Plugin registered via api.register()');

  // Register before_prompt_build Hook using api.on() (Plugin Hook API)
  api.on('before_prompt_build', async (event: any, ctx: any) => {
    const config: SoulMemoryConfig = {
      enabled: true,
      topK: 5,
      minScore: 0.0, // Legacy default
      ...api.config.plugins?.entries?.['soul-memory']?.config
    };

    logger.info('[Soul Memory] ✓ BEFORE_PROMPT_BUILD HOOK CALLED via api.on()');

    if (!config.enabled) {
      return {};
    }

    // BUGGY: Always fall back to parsing prompt tail, ignoring messages history
    const prompt = event.prompt || '';
    let lastUserMessage = prompt.trim();
    const lastNewlineIndex = lastUserMessage.lastIndexOf('\n');
    if (lastNewlineIndex >= 0) {
      lastUserMessage = lastUserMessage.substring(lastNewlineIndex + 1).trim();
    }

    // BUGGY: Never skips greetings/simple commands
    if (shouldSkipQuery(lastUserMessage)) {
      return {};
    }

    const query = extractQuery(lastUserMessage);

    if (!query || query.trim().length === 0) {
      return {};
    }

    logger.info(`[Soul Memory] Searching for: "${query}"`);

    // Search memories
    const results = await searchMemories(query, config);

    logger.info(`[Soul Memory] Found ${results.length} results`);

    if (results.length === 0) {
      return {};
    }

    // BUGGY: Injects raw memory context directly
    const memoryContext = buildMemoryContext(results, lastUserMessage);

    return {
      prependContext: memoryContext
    };
  });

  logger.info('[Soul Memory] Hook registered via api.on(): before_prompt_build');
}
