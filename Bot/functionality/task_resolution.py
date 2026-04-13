def resolve_task_candidates(results: list, query_title: str) -> tuple:
    """
    Given a list of results from Notion and the user's title query, 
    determine the best path forward.
    
    Returns (status, payload) where status is one of:
    - 'no_match': payload is None
    - 'resolved': payload is a single task dictionary
    - 'ambiguous': payload is a list of task candidate dictionaries
    """
    if not results:
        return "no_match", None
        
    if len(results) == 1:
        return "resolved", results[0]
        
    # We have multiple results. Check if one matches the query EXACTLY.
    # We need to extract the title safely from Notion properties.
    query_lower = query_title.lower().strip()
    
    exact_matches = []
    
    for r in results:
        props = r.get("properties", {})
        title_str = ""
        for k, v in props.items():
            if v.get("type") == "title":
                title_arr = v.get("title", [])
                if title_arr:
                    title_str = title_arr[0].get("text", {}).get("content", "")
                break
                
        if title_str.lower().strip() == query_lower:
            exact_matches.append(r)
            
    if len(exact_matches) == 1:
        # One task matched the exact wording exactly
        return "resolved", exact_matches[0]
        
    # Still ambiguous
    return "ambiguous", results
