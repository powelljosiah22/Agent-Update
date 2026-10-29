#!/bin/bash
input=$(cat)

search_path=$(echo "$input" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    args = data.get('toolArgs', {}) or data.get('arguments', {}) or {}
    if isinstance(args, str):
        args = json.loads(args)
    print(args.get('SearchPath', '') or args.get('SearchDirectory', ''))
except Exception:
    print('')
" 2>/dev/null)

decision="allow"
reason=""

# Block unconstrained root or home-directory crawls across all agents
if [ "$search_path" = "/" ] || [ "$search_path" = "$HOME" ] || [ "$search_path" = "~" ] || [ "$search_path" = "/Users" ]; then
  decision="deny"
  reason="STRICT BAN ON ROOT FILESYSTEM CRAWLING: Never run grep_search or find_by_name on HOME or root. Use semantic_search_obsidian first, or anchor Tier 2 grep strictly to a specific subfolder (e.g., 2_Parsed_MD/ or 2-Permanent-Notes/)."
fi

cat << JSON
{
  "decision": "$decision",
  "reason": "$reason"
}
JSON
