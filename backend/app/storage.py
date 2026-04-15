import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Create applications table once.
    We keep every decision as an audit log record.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            model_version TEXT NOT NULL,
            input_data TEXT NOT NULL,
            output_data TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_application(input_data: Dict[str, Any], output_data: Dict[str, Any], model_version: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO applications (created_at, model_version, input_data, output_data)
        VALUES (?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            model_version,
            json.dumps(input_data),
            json.dumps(output_data),
        ),
    )
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id


def _load_all_rows() -> List[tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, created_at, model_version, input_data, output_data FROM applications ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def list_applications() -> List[Dict[str, Any]]:
    rows = _load_all_rows()

    results = []
    for row in rows:
        input_data = json.loads(row[3])
        output_data = json.loads(row[4])
        results.append(
            {
                "application_id": row[0],
                "created_at": row[1],
                "model_version": row[2],
                "gender": input_data.get("gender", "unknown"),
                "risk_score": output_data["risk_score"],
                "risk_tier": output_data["risk_tier"],
                "recommended_decision": output_data["recommended_decision"],
                "confidence": output_data["confidence"],
            }
        )
    return results


def get_application_by_id(application_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, created_at, model_version, input_data, output_data FROM applications WHERE id = ?",
        (application_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "application_id": row[0],
        "created_at": row[1],
        "model_version": row[2],
        "input_data": json.loads(row[3]),
        "output_data": json.loads(row[4]),
    }


def portfolio_summary() -> Dict[str, Any]:
    apps = list_applications()

    if not apps:
        return {
            "total_applications": 0,
            "risk_tier_distribution": {"Low": 0, "Medium": 0, "High": 0, "Very High": 0},
            "decision_distribution": {"Approve": 0, "Conditional Approve": 0, "Decline": 0},
            "average_risk_score": 0.0,
        }

    tier_dist = {"Low": 0, "Medium": 0, "High": 0, "Very High": 0}
    decision_dist = {"Approve": 0, "Conditional Approve": 0, "Decline": 0}
    total_risk = 0.0

    for app in apps:
        tier_dist[app["risk_tier"]] += 1
        decision_dist[app["recommended_decision"]] += 1
        total_risk += app["risk_score"]

    return {
        "total_applications": len(apps),
        "risk_tier_distribution": tier_dist,
        "decision_distribution": decision_dist,
        "average_risk_score": round(total_risk / len(apps), 2),
    }


def model_metrics() -> Dict[str, Any]:
    summary = portfolio_summary()
    total = summary["total_applications"]

    if total == 0:
        return {
            "approval_rate": 0.0,
            "conditional_approval_rate": 0.0,
            "decline_rate": 0.0,
            "average_risk_score": 0.0,
            "expected_default_rate": 0.0,
        }

    decision_dist = summary["decision_distribution"]
    return {
        "approval_rate": round((decision_dist["Approve"] / total) * 100, 2),
        "conditional_approval_rate": round((decision_dist["Conditional Approve"] / total) * 100, 2),
        "decline_rate": round((decision_dist["Decline"] / total) * 100, 2),
        "average_risk_score": summary["average_risk_score"],
        # For this MVP, expected default rate is approximated by average model risk score.
        "expected_default_rate": summary["average_risk_score"],
    }


def fairness_report_by_gender() -> List[Dict[str, Any]]:
    apps = list_applications()
    segments = ["male", "female", "other", "unknown"]
    result = []

    for seg in segments:
        seg_apps = [a for a in apps if str(a.get("gender", "unknown")).lower() == seg]
        total = len(seg_apps)
        if total == 0:
            continue

        approvals = sum(1 for a in seg_apps if a["recommended_decision"] == "Approve")
        conditional = sum(1 for a in seg_apps if a["recommended_decision"] == "Conditional Approve")
        decline = sum(1 for a in seg_apps if a["recommended_decision"] == "Decline")

        result.append(
            {
                "segment": seg.title(),
                "total_applications": total,
                "approval_rate": round((approvals / total) * 100, 2),
                "conditional_approval_rate": round((conditional / total) * 100, 2),
                "decline_rate": round((decline / total) * 100, 2),
            }
        )
    return result


def score_trend() -> List[Dict[str, Any]]:
    rows = _load_all_rows()
    if not rows:
        return []

    day_bucket: Dict[str, Dict[str, float]] = {}
    for row in rows:
        created_at = row[1]
        output_data = json.loads(row[4])
        date_key = created_at[:10]
        if date_key not in day_bucket:
            day_bucket[date_key] = {"risk_sum": 0.0, "count": 0}
        day_bucket[date_key]["risk_sum"] += float(output_data.get("risk_score", 0.0))
        day_bucket[date_key]["count"] += 1

    points = []
    for date_key in sorted(day_bucket.keys()):
        count = int(day_bucket[date_key]["count"])
        avg = round(day_bucket[date_key]["risk_sum"] / count, 2) if count else 0.0
        points.append(
            {
                "date": date_key,
                "average_risk_score": avg,
                "application_count": count,
            }
        )
    return points