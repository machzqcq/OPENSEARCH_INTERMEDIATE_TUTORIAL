#!/usr/bin/env python3
"""
Convert all markdown files to PDF with mermaid diagram support.
Maintains folder hierarchy in output PDFS directory.
Uses markdown-it-py + mermaid-py to render mermaid diagrams as SVG, then converts to PDF.
"""

import os
import sys
from pathlib import Path
import subprocess
import re
import tempfile
import base64


def check_dependencies():
    """Check if required tools are installed."""
    # Check Python packages only
    missing_python = []
    required_packages = ['markdown', 'weasyprint', 'cairosvg']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_python.append(package)
            print(f"✗ {package} is NOT installed")
    
    # Check if mermaid-cli is available (optional but recommended)
    try:
        result = subprocess.run(['npx', '-y', '@mermaid-js/mermaid-cli', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ mermaid-cli is available via npx")
        else:
            print(f"⚠️  mermaid-cli not available (diagrams will be shown as code)")
    except Exception:
        print(f"⚠️  mermaid-cli not available (diagrams will be shown as code)")
    
    if missing_python:
        print("\n❌ Missing dependencies. Please install:")
        print(f"  - Python packages: pip install {' '.join(missing_python)}")
        return False
    
    return True


def find_markdown_files(base_path, target_folders):
    """Find all markdown files in target folders and root, excluding venv and node_modules."""
    markdown_files = []
    
    # Directories to exclude
    exclude_dirs = {'.venv', 'venv', 'node_modules', '__pycache__', '.git', 'snapshots', 'snapshots_old', 'snapshots_interns_all_old'}
    
    # Find markdown files in root directory
    for md_file in base_path.glob('*.md'):
        if md_file.is_file():
            markdown_files.append(md_file)
    
    # Find markdown files in target folders
    for folder in target_folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            print(f"⚠️  Folder not found: {folder}")
            continue
        
        # Find all .md files recursively, excluding certain directories
        for md_file in folder_path.rglob('*.md'):
            # Check if any excluded directory is in the path
            if any(excluded in md_file.parts for excluded in exclude_dirs):
                continue
            markdown_files.append(md_file)
    
    return sorted(markdown_files)


def process_mermaid_diagrams(content, temp_dir):
    """Extract mermaid diagrams, convert to PNG, and embed in markdown."""
    import markdown
    
    # Pattern to match mermaid code blocks
    mermaid_pattern = r'```mermaid\s*\n(.*?)\n```'
    
    # Quick check if there are any mermaid diagrams
    if not re.search(mermaid_pattern, content, re.DOTALL):
        return content
    
    mermaid_count = 0
    
    def replace_mermaid(match):
        nonlocal mermaid_count
        mermaid_count += 1
        mermaid_code = match.group(1)
        
        try:
            # Create temp file for mermaid code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, dir=temp_dir) as f:
                f.write(mermaid_code)
                mmd_file = f.name
            
            # Output PNG file instead of SVG
            png_file = mmd_file.replace('.mmd', '.png')
            
            # Create a config file to ensure fonts are properly rendered
            config_file = os.path.join(temp_dir, 'mermaid-config.json')
            with open(config_file, 'w') as f:
                f.write('''{
                    "theme": "default",
                    "themeVariables": {
                        "fontFamily": "Arial, Helvetica, sans-serif",
                        "fontSize": "16px"
                    },
                    "flowchart": {
                        "useMaxWidth": true,
                        "htmlLabels": true,
                        "curve": "basis"
                    }
                }''')
            
            # Try to use mermaid-cli (mmdc command) to generate PNG
            try:
                # Try mmdc first (if installed globally), otherwise use npx
                mmdc_cmd = ['mmdc', 
                     '-i', mmd_file, 
                     '-o', png_file, 
                     '-b', 'white',
                     '-c', config_file,
                     '-s', '2',
                     '--quiet']
                
                try:
                    result = subprocess.run(mmdc_cmd,
                        capture_output=True, 
                        text=True,
                        timeout=30)
                except FileNotFoundError:
                    # Fallback to npx if mmdc not found
                    mmdc_cmd[0:1] = ['npx', '-y', '@mermaid-js/mermaid-cli@10.6.1']
                    result = subprocess.run(mmdc_cmd,
                        capture_output=True, 
                        text=True,
                        timeout=30,
                        env={**os.environ, 'PUPPETEER_SKIP_CHROMIUM_DOWNLOAD': 'true'})
                
                if result.returncode != 0 or not os.path.exists(png_file):
                    raise Exception(f"mmdc failed")
                
                # Read PNG and encode as base64 data URI
                with open(png_file, 'rb') as f:
                    png_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Clean up temp files
                try:
                    os.unlink(mmd_file)
                    os.unlink(png_file)
                except:
                    pass
                
                # Return as embedded image in HTML
                return f'\n<div class="mermaid-diagram"><img src="data:image/png;base64,{png_data}" alt="Mermaid Diagram"/></div>\n'
                
            except Exception as e:
                # Clean up temp files
                try:
                    os.unlink(mmd_file)
                    if os.path.exists(png_file):
                        os.unlink(png_file)
                except:
                    pass
                raise e
            
        except Exception as e:
            # If conversion fails, return as formatted code block
            return f'\n<div class="mermaid-placeholder"><strong>[Mermaid Diagram]</strong><pre><code>{mermaid_code}</code></pre></div>\n'
    
    # Replace all mermaid blocks
    processed_content = re.sub(mermaid_pattern, replace_mermaid, content, flags=re.DOTALL)
    
    if mermaid_count > 0:
        print(f"    Processed {mermaid_count} mermaid diagram(s)")
    
    return processed_content


def convert_md_to_pdf(md_file, base_path, output_base):
    """Convert a single markdown file to PDF with mermaid support."""
    import markdown
    from weasyprint import HTML, CSS
    
    try:
        # Calculate relative path from base
        relative_path = md_file.relative_to(base_path)
        
        # Create output path maintaining hierarchy
        output_path = output_base / relative_path.parent / f"{md_file.stem}.pdf"
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Create temp directory for mermaid processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process mermaid diagrams
            has_mermaid = '```mermaid' in md_content
            if has_mermaid:
                md_content = process_mermaid_diagrams(md_content, temp_dir)
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                md_content,
                extensions=['extra', 'codehilite', 'tables', 'fenced_code', 'toc']
            )
            
            # Wrap in proper HTML structure with CSS
            full_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{md_file.stem}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            color: #333;
            max-width: 100%;
            overflow-wrap: break-word;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h1 {{ font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'DejaVu Sans Mono', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid #e1e4e8;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: bold;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 16px 0;
            padding-left: 16px;
            color: #666;
        }}
        .mermaid-diagram {{
            margin: 20px 0;
            text-align: center;
            page-break-inside: avoid;
        }}
        .mermaid-diagram svg {{
            max-width: 100%;
            height: auto;
        }}
        .mermaid-placeholder {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 6px;
        }}
        .mermaid-placeholder strong {{
            color: #6c757d;
            display: block;
            margin-bottom: 10px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 10px auto;
            page-break-inside: avoid;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
'''
            
            # Convert HTML to PDF
            HTML(string=full_html, base_url=str(md_file.parent)).write_pdf(str(output_path))
        
        print(f"✓ Converted: {relative_path} -> {output_path.relative_to(output_base)}")
        return True
            
    except Exception as e:
        print(f"✗ Error converting {md_file}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # Base path
    base_path = Path(__file__).parent.resolve()
    
    # Target folders to process
    target_folders = [
        "1. INSTALLATION_CONFIGURATION",
        "2. TRADITIONAL_SEARCH",
        "3. INGEST_AND_SEARCH_CONCEPTS",
        "4. AI_SEARCH",
        "5. AGENTIC_SEARCH",
        "6. REALTIME_PROJECTS"
    ]
    
    # Output directory
    output_base = base_path / "PDFS"
    
    print("=" * 80)
    print("Markdown to PDF Converter (with Mermaid Support)")
    print("=" * 80)
    print()
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print()
    print("=" * 80)
    print()
    
    # Find all markdown files
    print("Finding markdown files...")
    md_files = find_markdown_files(base_path, target_folders)
    
    if not md_files:
        print("❌ No markdown files found!")
        sys.exit(1)
    
    print(f"Found {len(md_files)} markdown files")
    print()
    print("=" * 80)
    print()
    
    # Create output directory
    output_base.mkdir(exist_ok=True)
    print(f"Output directory: {output_base}")
    print()
    
    # Convert each file
    print("Converting files...")
    print()
    
    success_count = 0
    fail_count = 0
    
    for md_file in md_files:
        if convert_md_to_pdf(md_file, base_path, output_base):
            success_count += 1
        else:
            fail_count += 1
    
    print()
    print("=" * 80)
    print("Conversion Summary")
    print("=" * 80)
    print(f"✓ Successful: {success_count}")
    print(f"✗ Failed: {fail_count}")
    print(f"📁 Output directory: {output_base}")
    print("=" * 80)
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
