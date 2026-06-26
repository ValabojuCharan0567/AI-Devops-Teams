from typing import Any, Dict, List
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


def fetch_database_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    database_url = settings.database_url
    if not database_url:
        return {
            "database_url": database_url,
            "evidence": ["Database is not configured; skipping database activity checks."],
            "results": {}
        }

    parsed = urlparse(database_url)
    evidence: List[str] = []
    results: Dict[str, Any] = {}

    try:
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432
        )

        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                try:
                    cursor.execute(
                        "SELECT datname, count(*) AS active_connections "
                        "FROM pg_stat_activity WHERE state = 'active' "
                        "GROUP BY datname ORDER BY active_connections DESC LIMIT 5"
                    )
                    active = cursor.fetchall()
                    results["active_connections"] = active
                    evidence.append(f"Found {len(active)} active database connection group(s)")
                except Exception as exc:
                    results["active_connections_error"] = str(exc)
                    evidence.append(f"Failed to query active connections: {exc}")

                try:
                    cursor.execute(
                        "SELECT usename, query, state, now() - query_start AS runtime "
                        "FROM pg_stat_activity WHERE state = 'active' "
                        "AND now() - query_start > interval '30 seconds' "
                        "ORDER BY runtime DESC LIMIT 5"
                    )
                    long_queries = cursor.fetchall()
                    results["long_running_queries"] = long_queries
                    if long_queries:
                        evidence.append(f"{len(long_queries)} long-running queries found")
                    else:
                        evidence.append("No long-running active queries detected")
                except Exception as exc:
                    results["long_running_queries_error"] = str(exc)
                    evidence.append(f"Failed to query long-running queries: {exc}")

                try:
                    cursor.execute(
                        "SELECT locktype, mode, granted, count(*) AS lock_count "
                        "FROM pg_locks GROUP BY locktype, mode, granted ORDER BY lock_count DESC LIMIT 5"
                    )
                    locks = cursor.fetchall()
                    results["locks"] = locks
                    if locks:
                        evidence.append(f"{len(locks)} lock groups observed in the database")
                    else:
                        evidence.append("No significant lock contention observed")
                except Exception as exc:
                    results["lock_query_error"] = str(exc)
                    evidence.append(f"Failed to query lock contention: {exc}")
    except Exception as exc:
        return {
            "database_url": database_url,
            "evidence": [f"Database connector error: {exc}"],
            "results": {"connection_error": str(exc)}
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return {
        "database_url": database_url,
        "evidence": evidence,
        "results": results
    }
