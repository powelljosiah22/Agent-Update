#!/usr/bin/env python3
import os
import sys
import json
import urllib.request

try:
    from dotenv import load_dotenv
    env_file = os.path.expanduser("~/Agents/Agent 0/.env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
except ImportError:
    pass


def send_response(response_dict):
    json_str = json.dumps(response_dict)
    sys.stdout.write(json_str + "\n")
    sys.stdout.flush()


def handle_initialize(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "obsidian_search",
                "version": "1.0.3"
            }
        }
    })


def handle_tools_list(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": [
                {
                    "name": "semantic_search_obsidian",
                    "description": "Perform hybrid BM25 + vector semantic search across Obsidian Second Brain notes and class materials (~140ms). Returns inline centered snippets (<3.8KB cap) with exact line numbers and file paths.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": { "type": "string", "description": "The search query or concept." },
                            "target": { "type": "string", "description": "Target search domain: 'vault' (Obsidian notes), 'classes' (textbooks/slides), or 'all' (both). Default is 'all'." },
                            "course": { "type": "string", "description": "Optional uppercase course code filter (e.g. 'SPA_3112', 'FIN_3105')." },
                            "chapter": { "type": "string", "description": "Optional chapter number or name (e.g. '4', 'Chapter 4')." },
                            "document_type": { "type": "string", "description": "Optional document type (e.g. 'slide', 'problem', 'textbook')." },
                            "n_results": { "type": "integer", "description": "Number of results to return (default 2-3 for inline precision)." },
                            "lexical_weight": { "type": "number", "description": "BM25 keyword weight vs vector similarity (0.2 = broad conceptual, 1.5 = balanced default, 3.0 = exact keyword precision)." },
                            "chunk_window": { "type": "integer", "description": "Dynamic chunk stitching slider: total number of adjacent chunks to stitch around each match (default 8; use 4-6 for surgical definitions, 12-20 for multi-page context)." }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "deep_research_obsidian",
                    "description": "Perform deep, multi-hop research across the Obsidian Second Brain and class materials. Automatically formulates 3 sub-queries, reads notes, and synthesizes a comprehensive cited answer.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": { "type": "string", "description": "The complex research question or topic to deeply investigate." },
                            "target": { "type": "string", "description": "Target domain: 'vault', 'classes', or 'all'. Default is 'all'." }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    })


def handle_tools_call(req_id, params):
    name = params.get("name")
    args = params.get("arguments", {})

    if name not in ["semantic_search_obsidian", "deep_research_obsidian"]:
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": "Method not found"}
        })
        return

    query = args.get("query", "")
    target = args.get("target", "all")
    course = args.get("course", "")
    chapter = args.get("chapter", "")
    document_type = args.get("document_type", "")
    n_results = args.get("n_results", 3)
    lexical_weight = args.get("lexical_weight", 1.5)
    chunk_window = args.get("chunk_window", 8)

    try:
        proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_handler)

        def query_chroma(q, n=3, t="all", c="", ch="", dt="", lw=1.5, cw=8):
            req = urllib.request.Request(
                "http://127.0.0.1:8085",
                data=json.dumps({
                    "query": q,
                    "n_results": n,
                    "target": t,
                    "course": c,
                    "chapter": ch,
                    "document_type": dt,
                    "lexical_weight": lw,
                    "chunk_window": cw
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with opener.open(req, timeout=60) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if "error" in res_data:
                    raise Exception(res_data["error"])
                return res_data.get("result", "No results found.")

        if name == "semantic_search_obsidian":
            final_text = query_chroma(query, n_results, target, course, chapter, document_type, lexical_weight, chunk_window)

        elif name == "deep_research_obsidian":
            gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_FREE_API_KEY", "")
            if gemini_key.startswith("__") or gemini_key.startswith("YOUR_") or not gemini_key:
                final_text = "GEMINI_API_KEY not found in environment. Falling back to single semantic search:\n\n" + query_chroma(query, 5, target, course, chapter, document_type, lexical_weight, chunk_window)
            else:
                def call_gemini_resilient(prompt, temp=0.1, timeout=12):
                    models_to_try = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash"]
                    last_e = None
                    for model_name in models_to_try:
                        try:
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                            payload = json.dumps({
                                "contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"temperature": temp}
                            }).encode("utf-8")
                            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                            with opener.open(req, timeout=timeout) as res:
                                data = json.loads(res.read().decode("utf-8"))
                                parts = data["candidates"][0]["content"]["parts"]
                                text = "".join([p.get("text", "") for p in parts]).strip()
                                if text:
                                    return text
                        except Exception as e:
                            last_e = e
                            continue
                    raise last_e

                queries = [query]
                try:
                    subq_prompt = f"""Given this research topic: '{query}', provide exactly 3 distinct search sub-queries for querying a hybrid BM25 + vector database of Obsidian notes and academic course materials.
To ensure comprehensive deep research, your 3 queries MUST follow this structure:
1. The exact targeted query or technical concept.
2. The broader parent category, theoretical framework, or overarching discipline.
3. Practical applications, exceptions, clinical/real-world examples, or related concepts.

Output ONLY a valid JSON array of 3 strings, no markdown."""
                    raw_subq = call_gemini_resilient(subq_prompt, temp=0.1, timeout=8)
                    text_out = raw_subq.strip()
                    if text_out.startswith("```json"):
                        text_out = text_out[7:]
                    elif text_out.startswith("```"):
                        text_out = text_out[3:]
                    if text_out.endswith("```"):
                        text_out = text_out[:-3]
                    parsed = json.loads(text_out.strip())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        queries = [str(q) for q in parsed[:3]]
                except Exception:
                    queries = [query]

                context = ""
                for q in queries:
                    context += f"--- Sub-Query: {q} ---\n{query_chroma(q, 2, target, course, chapter, document_type, lexical_weight, chunk_window)}\n\n"

                synth_prompt = f"Research Topic: {query}\n\nContext retrieved from Obsidian Vault and Course Notes:\n{context}\n\nSynthesize a comprehensive, multi-hop answer to the research topic using ONLY the context provided. Cite the files and notes."
                try:
                    final_text = call_gemini_resilient(synth_prompt, temp=0.2, timeout=20)
                except Exception as synth_err:
                    final_text = (
                        f"### Multi-Hop Research Results (Direct Context Aggregation)\n\n"
                        f"> [!NOTE]\n"
                        f"> Upstream synthesis model was temporarily busy ({synth_err}). Below is the aggregated multi-hop context retrieved across {len(queries)} sub-queries from your notes:\n\n"
                        f"{context}"
                    )

        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": final_text}]
            }
        })
    except Exception as e:
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(e)}
        })


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method")

        if method == "initialize":
            handle_initialize(req_id)
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            handle_tools_list(req_id)
        elif method == "tools/call":
            handle_tools_call(req_id, req.get("params", {}))
        elif req_id is not None:
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Method not found"}
            })


if __name__ == "__main__":
    main()
