# Source notes: Semantic text search using embeddings

Source: https://raw.githubusercontent.com/openai/openai-cookbook/main/examples/Semantic_text_search_using_embeddings.ipynb
Retrieved via WebFetch on 2026-07-02. Excerpted from a real OpenAI Cookbook notebook.

## Extracted factual material

The notebook is titled "Semantic text search using embeddings".

It explains that reviews can be searched semantically in an efficient and low-cost way by embedding a search query and then finding the most similar reviews. The dataset used in the notebook is created in a separate notebook about getting embeddings from a dataset.

The notebook reads a CSV file containing fine food reviews with embeddings. It uses pandas and NumPy, then converts the serialized embedding values into arrays.

The example compares cosine similarity between the embeddings of the query and the documents, then shows the top matching results.

A function named `search_reviews` takes a dataframe, a product description, and a number of results. It creates an embedding for the product description with `text-embedding-3-small`, calculates similarity between the product embedding and each stored review embedding, sorts by similarity in descending order, and returns the top results.

The notebook shows example searches such as "delicious beans", "whole wheat pasta", "bad delivery", "spoilt", and "pet food". In the "bad delivery" example, the matching review discusses excellent coffee but poor UPS delivery. The notebook explains that this can deliver value by quickly finding examples of delivery failures.

The "spoilt" example returns a review about a damaged metal cover and crushed cookies. The "pet food" example returns reviews about dog food for a dog with skin problems.

The notebook notes that search can be sped up with a special algorithm aimed at faster search through embeddings.

## Non-negotiable facts for the editor

- Semantic search compares embedded queries with embedded documents.
- The example uses cosine similarity to rank results.
- The workflow helps find meaning-related matches, not just exact keyword matches.
- The concrete examples include beans, whole wheat pasta, bad delivery, spoiled goods, and pet food.
- The business value shown in the notebook is quickly finding relevant review examples such as delivery failures.
