import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';
import { z } from 'zod';
import { findTicket } from '@/lib/tickets';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4o-mini'),
    system:
      'You are a support triage assistant. Look up ticket details before drafting an escalation note.',
    messages,
    tools: {
      lookupTicket: {
        description: 'Find a support ticket by id',
        parameters: z.object({
          id: z.string().describe('Ticket id such as INC-1057'),
        }),
        execute: async ({ id }) => findTicket(id),
      },
    },
  });

  return result.toDataStreamResponse();
}
