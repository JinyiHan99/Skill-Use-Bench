import { anthropic } from '@ai-sdk/anthropic';
import { generateObject, generateText } from 'ai';
import { z } from 'zod';

const reviewSchema = z.object({
  risk: z.enum(['low', 'medium', 'high']),
  summary: z.string(),
  followUps: z.array(z.string()),
});

export async function POST(req: Request) {
  const { transcript }: { transcript: string } = await req.json();

  const draft = await generateText({
    model: anthropic('claude-3-5-sonnet-latest'),
    prompt: `Summarize this customer interview for the product team:\n\n${transcript}`,
  });

  const { object } = await generateObject({
    model: anthropic('claude-3-5-sonnet-latest'),
    schema: reviewSchema,
    prompt: `Turn this summary into a structured product review:\n\n${draft.text}`,
  });

  return Response.json(object);
}
