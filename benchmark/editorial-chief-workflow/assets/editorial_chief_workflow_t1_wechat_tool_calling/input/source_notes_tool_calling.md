# Source notes: Chat model function/tool calling

Source: https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/How_to_call_functions_with_chat_models.ipynb
Retrieved via WebFetch on 2026-07-02. Excerpted from a real OpenAI Cookbook notebook.

## Extracted factual material

The notebook covers how to use the Chat Completions API in combination with external functions to extend the capabilities of GPT models.

`tools` is an optional parameter in the Chat Completion API which can be used to provide function specifications. The purpose of this is to enable models to generate function arguments which adhere to the provided specifications. The API will not actually execute any function calls. It is up to developers to execute function calls using model outputs.

Within the `tools` parameter, if the `functions` parameter is provided then by default the model will decide when it is appropriate to use one of the functions. The API can be forced to use a specific function by setting the `tool_choice` parameter to a specific function. The API can also be forced to not use any function by setting the `tool_choice` parameter to `none`.

If a function is used, the output will contain `finish_reason` with `tool_calls` in the response, as well as a `tool_calls` object that has the name of the function and the generated function arguments.

The notebook's overview includes two sections: how to generate function arguments, and how to call functions with model-generated arguments.

The basic concept section uses a hypothetical weather API to demonstrate function specifications. If a prompt asks about the current weather, the model may respond with clarifying questions. Once missing information is provided, it can generate appropriate function arguments.

The notebook also demonstrates forcing the model to use a specific function. Doing so can force the model to make assumptions about how to use it. It also demonstrates forcing the model not to use a function, which prevents the model from producing a proper function call.

Newer models such as gpt-5, gpt-4.1, or gpt-4o can call multiple functions in one turn.

The second part demonstrates executing functions whose inputs are model-generated and using this to implement an agent that can answer questions about a database. For simplicity it uses the Chinook sample database. The notebook notes that SQL generation can be high-risk in a production environment because models are not perfectly reliable at generating correct SQL.

A later section defines utility functions to extract a representation of the database schema. The database schema is inserted into the function specification so the model can know about it.

The described execution loop has four steps: prompt the model with content that may result in a tool selection; check programmatically whether the model wanted to call a function; extract the function name and parameters, call the function with those parameters, and append the result to messages; then invoke the chat completions API again with the message list to get the response.

## Non-negotiable facts for the editor

- The API generates function arguments but does not execute external functions itself.
- Developers are responsible for executing calls based on model outputs.
- Missing information should lead to clarification instead of blind assumptions.
- Forcing tool choice can make the model assume inputs.
- SQL generation with model outputs is high-risk in production.
