'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages, input, handleInputChange, append, isLoading } = useChat({
    api: '/api/chat',
  });

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-4 p-6">
      <h1 className="text-xl font-semibold">Customer reply assistant</h1>
      <section className="flex-1 space-y-3 rounded border p-4">
        {messages.map(message => (
          <article key={message.id} className="rounded bg-zinc-50 p-3">
            <p className="text-xs uppercase text-zinc-500">{message.role}</p>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </article>
        ))}
      </section>
      <form
        className="flex gap-2"
        onSubmit={event => {
          event.preventDefault();
          if (!input.trim()) return;
          append({ role: 'user', content: input });
        }}
      >
        <input
          className="flex-1 rounded border px-3 py-2"
          value={input}
          onChange={handleInputChange}
          placeholder="Ask about the support thread..."
        />
        <button className="rounded bg-black px-4 py-2 text-white" disabled={isLoading}>
          Send
        </button>
      </form>
    </main>
  );
}
