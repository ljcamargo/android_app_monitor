import os
import json
import argparse
import glob
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess
import pandas as pd

load_dotenv()

def get_latest_data_file():
    list_of_files = glob.glob('data/vitals_*.json')
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def call_gemini(prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    response = model.generate_content(prompt)
    return response.text

def call_local_llm(prompt):
    local_command = os.getenv("LOCAL_LLM_COMMAND")
    if not local_command:
        raise ValueError("LOCAL_LLM_COMMAND not found in environment")
    
    # Example: LOCAL_LLM_COMMAND="ollama run llama3"
    # We'll append the prompt or pipe it
    try:
        process = subprocess.Popen(local_command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=prompt)
        if process.returncode != 0:
            print(f"Local LLM Error: {stderr}")
            return None
        return stdout
    except Exception as e:
        print(f"Error calling local LLM: {e}")
        return None

def format_reviews_for_prompt(reviews_data):
    """
    Formats user reviews data into a readable markdown section.
    """
    if not reviews_data or reviews_data.get("count", 0) == 0:
        return "No user reviews available for this period."
    
    parts = []
    parts.append(f"Total reviews fetched: {reviews_data['count']}")
    parts.append("")
    
    for i, rev in enumerate(reviews_data["latest"], 1):
        parts.append(f"### Review {i}")
        parts.append(f"- **Author:** {rev.get('authorName', 'Anonymous')}")
        parts.append(f"- **Rating:** {rev.get('starRating', 'N/A')} stars")
        parts.append(f"- **Date:** {rev.get('lastModified', 'unknown')}")
        parts.append(f"- **Language:** {rev.get('reviewerLanguage', 'N/A')}")
        parts.append(f"- **App Version:** {rev.get('appVersionName', 'N/A')}")
        parts.append(f"- **Thumbs Up:** {rev.get('thumbsUpCount', 0)}  |  **Thumbs Down:** {rev.get('thumbsDownCount', 0)}")
        
        text = rev.get('text', '')
        if text:
            # Truncate very long reviews to keep prompt manageable
            if len(text) > 500:
                text = text[:500] + "..."
            parts.append(f"- **Comment:** {text}")
        else:
            parts.append("- **Comment:** (no text)")
        parts.append("")
    
    return "\n".join(parts)

def format_data_for_prompt(metrics_data):
    formatted_sections = []
    for metric_name, data in metrics_data.items():
        if not data or 'rows' not in data or not data['rows']:
            formatted_sections.append(f"### {metric_name}\nNo events reported or data unavailable for this period (this typically means 0 errors/events).")
            continue
        
        # Define metric labels based on the metric type
        main_metric_label = metric_name
        metric_labels = [main_metric_label, "Distinct Users"]
        
        if metric_name == "errorCounts":
             metric_labels = ["Error Report Count", "Distinct Users"]
        
        rows = []
        for row in data['rows']:
            date = f"{row['startTime']['year']}-{row['startTime']['month']}-{row['startTime']['day']}"
            
            row_data = {'Date': date}
            
            # Add dimensions if present
            if 'dimensions' in row:
                for dim in row['dimensions']:
                    # Use the dimension name from the API response
                    dim_label = dim['dimension']
                    # Use the first available value (usually just one)
                    if 'stringValue' in dim:
                        row_data[dim_label] = dim['stringValue']
                    elif 'int64Value' in dim:
                        row_data[dim_label] = dim['int64Value']
            
            for i, m_val in enumerate(row['metrics']):
                label = metric_labels[i] if i < len(metric_labels) else f"Value_{i+1}"
                
                value = "N/A"
                if 'decimalValue' in m_val:
                    value = m_val['decimalValue']['value']
                elif 'integerValue' in m_val:
                    value = m_val['integerValue']['value']
                
                row_data[label] = value
            
            rows.append(row_data)
        
        df = pd.DataFrame(rows)
        formatted_sections.append(f"### {metric_name}\n{df.to_markdown(index=False)}")
    
    return "\n\n".join(formatted_sections)

def generate_prompt(app_package, data):
    formatted_metrics = format_data_for_prompt(data['metrics'])
    
    prompt = f"""
Analyze the following Google Play Vitals data for the app '{app_package}' and provide a brief report in Markdown.
The data covers the period from {data['period']['start']} to {data['period']['end']}.

Data:
{formatted_metrics}

Please include:
1. A summary of the app's health (ANR, Crash rates, etc.).
2. Any significant trends or issues detected (variations among days).
3. Recommendations for improvement.
4. Keep it concise but informative.

The output must be in Markdown format.
"""
    
    # If reviews data is present, append a user feedback analysis section
    if "reviews" in data:
        formatted_reviews = format_reviews_for_prompt(data["reviews"])
        prompt += f"""

---

## User Reviews Analysis

Below are the latest user reviews for '{app_package}'. Please analyze them and incorporate your findings into the report above.

{formatted_reviews}

When analyzing these reviews, please:
1. Identify the most common praises and complaints.
2. Note any sentiment trends (positive, negative, mixed).
3. Correlate user feedback with the vitals data where possible (e.g., users complaining about crashes when crashRate is high).
4. Suggest specific improvements based on user feedback.

Integrate these findings naturally into the report sections above rather than as a separate block.
"""
    
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Generate LLM reports from fetched data.")
    parser.add_argument("--file", type=str, help="Specific JSON file to process (defaults to latest)")
    parser.add_argument("--local", action="store_true", help="Use local LLM instead of Gemini")
    
    args = parser.parse_args()
    
    data_file = args.file if args.file else get_latest_data_file()
    
    if not data_file:
        print("No data files found in data/ directory.")
        return
    
    print(f"Processing data from {data_file}...")
    
    with open(data_file, 'r') as f:
        all_data = json.load(f)
        
    for pkg, data in all_data.items():
        print(f"Generating report for {pkg}...")
        prompt = generate_prompt(pkg, data)
        
        if args.local:
            report = call_local_llm(prompt)
        else:
            report = call_gemini(prompt)
        
        if report:
            report_filename = data_file.replace(".json", f"_{pkg.replace('.', '_')}.md")
            with open(report_filename, "w") as f:
                f.write(report)
            print(f"Report saved to {report_filename}")
        else:
            raise ValueError(f"Failed to generate report for {pkg}")

if __name__ == "__main__":
    main()
