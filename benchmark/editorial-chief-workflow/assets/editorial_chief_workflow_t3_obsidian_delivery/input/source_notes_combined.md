# Source notes for review-ready Obsidian article

Sources:
- https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_call_functions_with_chat_models.ipynb
- https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/Semantic_text_search_using_embeddings.ipynb

Retrieved via WebFetch on 2026-07-02. Excerpted from real OpenAI Cookbook notebooks.

## Facts about model tool/function calling

The Chat Completions API can use a `tools` parameter to provide function specifications. This enables models to generate function arguments that follow the provided specifications. The API does not execute the function calls itself; developers must execute calls using model outputs.

By default, the model can decide when it is appropriate to use a function. Developers can force the model to use a specific function, but doing so can force assumptions. Developers can also force the model not to use a function.

When a function is used, the response contains an indicator that tool calls were selected and includes the function name and generated arguments. Newer models can call multiple functions in one turn.

The notebook demonstrates an agent that answers questions about a database by using model-generated inputs. It warns that SQL generation can be high-risk in production because models are not perfectly reliable at generating correct SQL.

## Facts about embeddings search

Semantic text search can embed a query and find the most similar embedded documents. The cookbook example uses food reviews with stored embeddings. It compares cosine similarity between the query embedding and review embeddings, sorts by similarity, and returns top matches.

Example queries include "delicious beans", "whole wheat pasta", "bad delivery", "spoilt", and "pet food". The delivery example shows a review where the coffee was excellent but the UPS delivery was poor. The notebook explains that this can quickly find examples of delivery failures.

## Editorial boundary notes

- Keep the contrast between tool calling and embeddings search clear.
- Do not claim the API executes external tools by itself.
- Do not treat semantic search as exact keyword matching.
- Mention production caution around model-generated SQL only as a practical risk, not as a general rejection of the method.
