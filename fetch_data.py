import os
import json
import argparse
import time
import re
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

def get_reporting_service():
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Service account file not found at {credentials_path}")
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/playdeveloperreporting"]
    )
    return build("playdeveloperreporting", "v1beta1", credentials=credentials)

import re
from googleapiclient.errors import HttpError

def execute_with_freshness_check(resource, name, body):
    """
    Executes a query and retries if a freshness error occurs by adjusting the end date.
    Returns (response, adjusted_date_dict or None)
    """
    try:
        return resource.query(name=name, body=body).execute(), None
    except HttpError as e:
        error_msg = str(e)
        if "field should be at most the current freshness" in error_msg:
            match = re.search(r"freshness (\d{4}-\d{2}-\d{2})", error_msg)
            if match:
                fresh_date_str = match.group(1)
                print(f"  Adjusting end_date to freshness: {fresh_date_str}")
                fresh_date = datetime.strptime(fresh_date_str, "%Y-%m-%d")
                
                new_end_time = {
                    "year": fresh_date.year,
                    "month": fresh_date.month,
                    "day": fresh_date.day
                }
                body["timelineSpec"]["endTime"] = new_end_time
                return resource.query(name=name, body=body).execute(), new_end_time
        raise e

def fetch_vitals(service, package_name, start_date, end_date):
    """
    Fetches ANR, Crash, and other vitals for a given package.
    """
    data = {"package_name": package_name, "metrics": {}}
    
    current_timeline_spec = {
        "aggregationPeriod": "DAILY",
        "startTime": {
            "year": start_date.year,
            "month": start_date.month,
            "day": start_date.day
        },
        "endTime": {
            "year": end_date.year,
            "month": end_date.month,
            "day": end_date.day
        }
    }

    vitals_methods = [
        # (metric_id, method_name, resource_suffix, required_dimensions, body_metric_id)
        ("anrRate", "anrrate", "anrRateMetricSet", [], "anrRate"),
        ("crashRate", "crashrate", "crashRateMetricSet", [], "crashRate"),
        ("slowStartRate", "slowstartrate", "slowStartRateMetricSet", ["startType"], "slowStartRate"),
        ("stuckBackgroundWakelockRate", "stuckbackgroundwakelockrate", "stuckBackgroundWakelockRateMetricSet", [], "stuckBgWakelockRate"),
        ("excessiveWakeupRate", "excessivewakeuprate", "excessiveWakeupRateMetricSet", [], "excessiveWakeupRate")
    ]
    
    vitals_resource = service.vitals()
    for label, method_name, resource_suffix, dims, metric_id in vitals_methods:
        print(f"  Fetching {label}...")
        resource = getattr(vitals_resource, method_name)()
        body = {
            "timelineSpec": current_timeline_spec,
            "metrics": [metric_id, "distinctUsers"]
        }
        if dims:
            body["dimensions"] = dims
        
        response, adjusted_end_time = execute_with_freshness_check(resource, f"apps/{package_name}/{resource_suffix}", body)
        if adjusted_end_time:
            current_timeline_spec["endTime"] = adjusted_end_time
        
        if not response:
            response = {'rows': []}
            
        data["metrics"][label] = response
        time.sleep(0.15)

    # Adding Error Counts (Crashes + ANRs)
    print(f"  Fetching errorCounts...")
    body = {
        "timelineSpec": current_timeline_spec,
        "metrics": ["errorReportCount", "distinctUsers"],
        "dimensions": ["reportType"]
    }
    response, adjusted_end_time = execute_with_freshness_check(
        service.vitals().errors().counts(), 
        f"apps/{package_name}/errorCountMetricSet", 
        body
    )
    if adjusted_end_time:
        current_timeline_spec["endTime"] = adjusted_end_time
    
    if not response:
        response = {'rows': []}
        
    data["metrics"]["errorCounts"] = response
    time.sleep(0.15)

    data["period"] = {
        "start": start_date.isoformat(),
        "end": end_date.isoformat()
    }
    return data

def main():
    parser = argparse.ArgumentParser(description="Fetch Google Play Vitals data.")
    parser.add_argument("--packages", type=str, help="Comma separated list of package names")
    parser.add_argument("--days", type=int, default=7, help="Number of days to fetch data for")
    
    args = parser.parse_args()
    
    package_names = []
    if args.packages:
        package_names = [p.strip() for p in args.packages.split(",")]
    elif os.getenv("PACKAGE_NAMES"):
        package_names = [p.strip() for p in os.getenv("PACKAGE_NAMES").split(",")]
    else:
        raise ValueError("No package names provided. Use --packages or set PACKAGE_NAMES in .env")

    service = get_reporting_service()
    
    # Start and end dates must be in the past.
    # The API usually has a delay of 3-5 days (freshness).
    # We'll start with a 2-day lag and let the dynamic retry logic 
    # adjust it based on the actual API freshness if needed.
    end_date_dt = datetime.utcnow() - timedelta(days=2)
    start_date_dt = end_date_dt - timedelta(days=args.days)
    
    # Ensure endTime is after startTime
    end_date_inclusive = end_date_dt + timedelta(days=1)
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_data = {}
    for pkg in package_names:
        print(f"Fetching data for {pkg}...")
        data = fetch_vitals(service, pkg.strip(), start_date_dt, end_date_inclusive)
        all_data[pkg] = data
            
    filename = f"vitals_{timestamp}.json"
    filepath = os.path.join(data_dir, filename)
    
    with open(filepath, "w") as f:
        json.dump(all_data, f, indent=2)
        
    print(f"Data saved to {filepath}")

if __name__ == "__main__":
    main()
