# app.py
import os, shlex, json
from datetime import datetime
from client import load_clients
from dotenv import load_dotenv
import requests

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  

def ask_llm(history, user_text):
    if not ANTHROPIC_API_KEY:
        history.append(("assistant","(LLM stub) usa /music:<tool> ..."))
        return history[-1][1]
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 256,
        "messages": [{"role":"user","content":user_text}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    reply = data.get("content",[{"text":"(respuesta)"}])[0].get("text","(respuesta)")
    history.append(("assistant", reply))
    return reply

def log(line: str):
    os.makedirs("logs", exist_ok=True)
    with open("logs/mcp.log","a",encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {line}\n")

def parse_cmd(line: str):
    if not line.startswith("/"): return None
    parts = shlex.split(line[1:])
    head = parts[0]
    server, tool = head.split(":") if ":" in head else (head, None)
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v.strip('"')
    return server, tool, params

def main():
    print("CLI MCP listo. Formato: /<server>:<tool> key=val ... | texto libre → LLM | /salir")
    print("Ejemplos (tu server):")
    print("  /music:create_mood_playlist mood=happy size=8")
    print("  /music:find_similar_songs song_name=\"cruel summer\" count=5")
    print("  /music:analyze_song song_name=\"cardigan\"")
    print("  /music:create_genre_playlist genres=\"pop,rock\" size=12 diversity=high")
    print("  /music:get_dataset_stats\n")

    clients = load_clients("servers.yaml")
    history = []

    try:
        while True:
            s = input("> ").strip()
            if s.lower() in ("/salir","/exit"): break

            parsed = parse_cmd(s)
            if parsed:
                server, tool, params = parsed
                if server not in clients:
                    print(f"Servidor desconocido: {server}"); continue
                if not tool:
                    print("Falta tool: usa /server:tool"); continue

                # soporta listas tipo genres="pop,rock"
                for k,v in list(params.items()):
                    if k in ("genres",) and isinstance(v,str):
                        params[k] = [x.strip() for x in v.split(",") if x.strip()]
                    if k in ("size","count","min_popularity"):
                        try: params[k] = int(v)
                        except: pass

                try:
                    log(f"→ {server}:{tool} {params}")
                    res = clients[server].call(tool, params)
                    print(res if isinstance(res,str) else json.dumps(res, ensure_ascii=False, indent=2))
                    log(f"← {server}:{tool} {res}")
                except Exception as e:
                    print("Error:", e); log(f"ERR {server}:{tool} {e}")
            else:
                history.append(("user", s))
                reply = ask_llm(history, s)
                print(reply)
    finally:
        for c in clients.values():
            try: c.close()
            except: pass

if __name__ == "__main__":
    main()
