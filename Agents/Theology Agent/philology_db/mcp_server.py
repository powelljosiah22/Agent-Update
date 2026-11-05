#!/usr/bin/env python3
"""
MCP Server for the Biblical Philological Engine (biblical-philology)
Exposes:
  1. vector_concept_lookup
  2. sql_concordance_query
"""
import sys
import json
from philology_engine import vector_concept_lookup, sql_concordance_query


def send_response(response_dict):
    sys.stdout.write(json.dumps(response_dict) + "\n")
    sys.stdout.flush()


def handle_initialize(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "biblical-philology", "version": "1.0.0"},
        },
    })


def handle_tools_list(req_id):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": [
                {
                    "name": "vector_concept_lookup",
                    "description": "Concept-to-Lemma Router: Queries the hybrid ChromaDB + SQLite lexicon index to map an English concept, Greek/Hebrew word, or transliteration to the top candidate ancient root_lemma IDs and Strong's numbers with corpus counts across OT, LXX, and NT.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "English concept (e.g. 'atonement', 'covenant loyalty', 'justification'), transliteration ('chesed', 'dikaiosyne'), or Strong's ID."},
                            "language_filter": {"type": "string", "description": "Optional language filter: 'all', 'Hebrew', 'Aramaic', or 'Greek'. Default 'all'."},
                            "n_results": {"type": "integer", "description": "Number of candidate lemmas to return (default 8)."},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "sql_concordance_query",
                    "description": "Deterministic SQLite morphological, interlinear, and concordance engine over the 66-book Hebrew/Aramaic OT (WLC), Greek NT (SBLGNT), and Greek Septuagint (LXX Rahlfs 1935).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["interlinear", "lemma", "lxx_bridge", "custom_sql", "dispersion", "verify"],
                                "description": "'interlinear' (verse/range word-by-word table), 'lemma' (concordance + morph distribution for a root_lemma/Strong's ID), 'lxx_bridge' (traces Hebrew OT <-> Greek LXX translation equivalents), 'custom_sql' (raw read-only SELECT query), 'dispersion' (length-normalized canonical genre spread for a comma-separated lemma cluster in lemma_id), or 'verify' (claim ledger: pass 'Ref=lemma; Ref=lemma' in sql_query).",
                            },
                            "reference": {"type": "string", "description": "For mode='interlinear': Scripture reference (e.g., 'Gen 1:1', 'Rom 3:21-25', 'Ps 23:1-3')."},
                            "lemma_id": {"type": "string", "description": "For mode='lemma' or 'lxx_bridge': root_lemma or Strong's ID (e.g., 'H2617', 'G1343', 'λόγος', 'πίστις')."},
                            "sql_query": {"type": "string", "description": "For mode='custom_sql': read-only SELECT. For mode='verify': claims like 'Luke 12:33=G4453; 2Cor 8:13=ἰσότης'."},
                            "claims": {"type": "string", "description": "For mode='verify': semicolon-separated claims like 'Luke 12:33=G4453; 2Cor 8:13=G2471; Eccl 5:18=H7980'."},
                            "testament": {"type": "string", "description": "Filter by testament: 'all', 'OT', 'NT', or 'LXX'. Default 'all'."},
                            "limit": {"type": "integer", "description": "Maximum concordance rows to return (default 25)."},
                        },
                        "required": ["mode"],
                    },
                },
            ]
        },
    })


def handle_tools_call(req_id, params):
    name = params.get("name")
    args = params.get("arguments", {})
    try:
        if name == "vector_concept_lookup":
            out = vector_concept_lookup(
                query=args.get("query", ""),
                language_filter=args.get("language_filter", "all"),
                n_results=int(args.get("n_results", 8)),
            )
        elif name == "sql_concordance_query":
            out = sql_concordance_query(
                mode=args.get("mode", "interlinear"),
                reference=args.get("reference", ""),
                lemma_id=args.get("lemma_id", ""),
                sql_query=args.get("claims") or args.get("sql_query") or args.get("reference", ""),
                testament=args.get("testament", "all"),
                limit=int(args.get("limit", 25)),
            )
        else:
            send_response({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {name}"}})
            return

        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": out}]},
        })
    except Exception as e:
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": f"Error executing {name}: {str(e)}"}], "isError": True},
        })


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        req_id = req.get("id")
        method = req.get("method", "")
        if method == "initialize":
            handle_initialize(req_id)
        elif method == "tools/list":
            handle_tools_list(req_id)
        elif method == "tools/call":
            handle_tools_call(req_id, req.get("params", {}))
        elif req_id is not None:
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})


if __name__ == "__main__":
    main()
