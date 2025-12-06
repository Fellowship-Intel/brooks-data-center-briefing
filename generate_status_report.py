# generate_status_report.py
"""
Script to generate a comprehensive status report for the Brooks application.
It collects:
- Codebase overview (file count, language breakdown)
- Test results via pytest
- Summaries from key documentation files
- Deployment readiness indicators
The output is written to `Brooks status number one.md` in the project root.
"""
import os
import sys
from datetime import datetime
import subprocess
from pathlib import Path
import re

def count_files_by_extension(root: Path):
    counts = {}
    for file_path in root.rglob('*'):
        if file_path.is_file():
            # Skip .git and node_modules for cleaner stats if desired, 
            # but user might want everything. Let's keep it simple.
            ext = file_path.suffix.lower()
            counts[ext] = counts.get(ext, 0) + 1
    return counts

def get_test_results():
    try:
        # Run pytest in quiet mode, capture summary line
        result = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=str(Path.cwd()), capture_output=True, text=True, check=False)
        output = result.stdout.strip()
        
        # Robust parsing: look for patterns independently
        # Example output: "37 passed, 8 skipped in 0.45s" or "32 failed, 37 passed..."
        passed = 0
        failed = 0
        skipped = 0
        
        m_passed = re.search(r"(\d+)\s+passed", output)
        if m_passed: passed = int(m_passed.group(1))
        
        m_failed = re.search(r"(\d+)\s+failed", output)
        if m_failed: failed = int(m_failed.group(1))
        
        m_skipped = re.search(r"(\d+)\s+skipped", output)
        if m_skipped: skipped = int(m_skipped.group(1))
        
        total = passed + failed + skipped
        
        if total == 0 and "passed" not in output and "failed" not in output:
             return {"total": None, "passed": None, "failed": None, "skipped": None, "raw": output}
             
        return {"total": total, "passed": passed, "failed": failed, "skipped": skipped}
    except Exception as e:
        return {"error": str(e)}

def read_doc_section(path: Path, max_lines: int = 200):
    if not path.is_file():
        return "File not found."
    try:
        with path.open('r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line.rstrip())
            return "\n".join(lines)
    except Exception as e:
        return f"Error reading file: {e}"

def main():
    project_root = Path.cwd()
    report_path = project_root / "Brooks status number one.md"
    
    # 1. Codebase overview
    file_counts = count_files_by_extension(project_root)
    total_files = sum(file_counts.values())
    
    # 2. Test results
    test_results = get_test_results()
    
    # 3. Documentation snippets
    docs = {
        "README": read_doc_section(project_root / "README.md"),
        "IMPLEMENTATION_COMPLETE": read_doc_section(project_root / "IMPLEMENTATION_COMPLETE.md"),
        "DEPLOYMENT_VERIFICATION": read_doc_section(project_root / "DEPLOYMENT_VERIFICATION.md"),
    }
    
    # Build markdown report
    lines = []
    lines.append("# Brooks Status Number One")
    lines.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    lines.append("## Codebase Overview")
    lines.append(f"- Total files: {total_files}")
    # Sort by count desc
    for ext, cnt in sorted(file_counts.items(), key=lambda x: (-x[1], x[0])):
         if cnt > 0:
            lines.append(f"  - *{ext or 'no extension'}*: {cnt}")
            
    lines.append("\n## Test Results")
    if "error" in test_results:
        lines.append(f"Error running tests: {test_results['error']}")
    else:
        if test_results.get('total') is None:
             lines.append(f"Tests not run or no results found. Raw output: {test_results.get('raw', 'None')}")
        else:
            lines.append(f"- Total tests: {test_results.get('total', 'N/A')}")
            lines.append(f"- Passed: {test_results.get('passed', '0')}")
            lines.append(f"- Failed: {test_results.get('failed', '0')}")
            lines.append(f"- Skipped: {test_results.get('skipped', '0')}")
            
    lines.append("\n## Documentation Summary")
    for name, content in docs.items():
        lines.append(f"### {name}")
        lines.append(content if content else "(empty)")
        lines.append("\n---\n")
        
    # Write report
    report_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()
