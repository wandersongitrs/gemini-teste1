# -*- coding: utf-8 -*-
"""
Relatórios simples de uso do bot (analytics)

Gera métricas básicas a partir do banco SQLite:
- Total de mensagens por "role"
- Top comandos mais usados
- Janelas de uso por hora

Uso:
  python analytics.py
"""

import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Tuple

DB_FILE = "bot_data.db"


def connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_FILE)


def summarize_roles(conn: sqlite3.Connection) -> Dict[str, int]:
    cur = conn.cursor()
    cur.execute("SELECT role, COUNT(1) FROM chat_history GROUP BY role")
    return {row[0]: int(row[1]) for row in cur.fetchall()}


def top_commands(conn: sqlite3.Connection, top_n: int = 10) -> Dict[str, int]:
    """Conta comandos mais usados (linhas de chat_history que começam com /)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT content FROM chat_history WHERE role = 'user' AND content LIKE '/%'"
    )
    counts = Counter()
    for (content,) in cur.fetchall():
        cmd = content.split()[0].strip()
        counts[cmd] += 1
    return dict(counts.most_common(top_n))


def usage_by_hour(conn: sqlite3.Connection) -> Dict[str, int]:
    """Distribuição de mensagens por hora (UTC)."""
    cur = conn.cursor()
    cur.execute("SELECT timestamp FROM chat_history")
    buckets = Counter()
    for (ts,) in cur.fetchall():
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            # Fallback: tentar formato padrão SQLite
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
        hour = dt.strftime("%Y-%m-%d %H:00")
        buckets[hour] += 1
    # Ordenar
    return dict(sorted(buckets.items()))


def main():
    try:
        with connect() as conn:
            print("\n=== RESUMO DE USO ===")
            roles = summarize_roles(conn)
            for role, count in roles.items():
                print(f"{role:>8}: {count}")

            print("\n=== TOP COMANDOS ===")
            cmds = top_commands(conn)
            if cmds:
                for cmd, cnt in cmds.items():
                    print(f"{cmd:>16}: {cnt}")
            else:
                print("(sem comandos registrados)")

            print("\n=== USO POR HORA (UTC) ===")
            per_hour = usage_by_hour(conn)
            if per_hour:
                for bucket, cnt in per_hour.items():
                    print(f"{bucket}: {cnt}")
            else:
                print("(sem tráfego)")

            print("\nOK")
    except sqlite3.Error as e:
        print(f"Erro ao ler banco: {e}")


if __name__ == "__main__":
    main()


