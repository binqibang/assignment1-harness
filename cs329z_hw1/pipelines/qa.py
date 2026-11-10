import json
from typing import Callable
from cs329z_hw1.pipelines.prompts import QA_PROMPT
from cs329z_hw1.types import Email, LMCallable


def run(    
    question: str,
    search: Callable[[str, int], list[Email]],
    lm: LMCallable,
    max_hops: int = 3
) -> dict:
    search_history = []
    start_messsage = [{'role': 'system', 'content': QA_PROMPT}]

    for hop in range(max_hops):
        # Build the current state
        current_state = {
            "question": question,
            "hop_count": hop,
            "search_history": search_history
        }

        # Call the language model with the current state
        messages = start_messsage + [{'role': 'user', 'content': current_state}]
        lm_response = lm(messages)

        try:
            response = json.loads(lm_response)
        except json.JSONDecodeError:
            return {"answer": None, "support": []}

        if response.get("action") == "search":
            query = response.get("query", "")
            k = response.get("k", 5)
            search_results = search(query, k)
            search_history.append({
                "query": query,
                "results": [{"id": email["id"], "content": email["body"]} for email in search_results]
            })
        else:
            return {
                "answer": response.get("answer"),
                "support": response.get("support", [])
            }
