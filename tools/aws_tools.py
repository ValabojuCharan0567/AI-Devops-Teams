from datetime import datetime, timedelta
from typing import Any, Dict, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


def fetch_aws_activity(incident: Dict[str, Any]) -> Dict[str, Any]:
    region = settings.aws_region
    evidence: List[str] = []
    alarms = []
    bad_instances = []
    db_instances = []

    if not region:
        return {
            "region": region,
            "alarms": [],
            "ec2_non_running": [],
            "rds_instances": [],
            "evidence": ["AWS region not configured; skipping AWS activity checks."]
        }

    try:
        cw = boto3.client("cloudwatch", region_name=region)
        ec2 = boto3.client("ec2", region_name=region)
        rds = boto3.client("rds", region_name=region)

        alarms = cw.describe_alarms(StateValue="ALARM").get("MetricAlarms", [])
        if alarms:
            evidence.append(f"{len(alarms)} CloudWatch alarm(s) currently in ALARM state")
        else:
            evidence.append("No CloudWatch alarms in ALARM state.")

        instances = ec2.describe_instance_status(IncludeAllInstances=True).get("InstanceStatuses", [])
        bad_instances = [i["InstanceId"] for i in instances if i.get("InstanceState", {}).get("Name") != "running"]
        if bad_instances:
            evidence.append(f"Non-running EC2 instances: {', '.join(bad_instances[:3])}")
        else:
            evidence.append("All queried EC2 instances are running.")

        db_instances = rds.describe_db_instances().get("DBInstances", [])
        if db_instances:
            evidence.append(f"{len(db_instances)} RDS instance(s) found")
        else:
            evidence.append("No RDS instances were discovered.")

    except (BotoCoreError, ClientError) as exc:
        evidence.append(f"AWS connector error: {exc}")
    except Exception as exc:
        evidence.append(f"AWS connector unexpected error: {exc}")

    return {
        "region": region,
        "alarms": [alarm.get("AlarmName") for alarm in alarms] if alarms else [],
        "ec2_non_running": bad_instances,
        "rds_instances": [db["DBInstanceIdentifier"] for db in db_instances] if db_instances else [],
        "evidence": evidence
    }
