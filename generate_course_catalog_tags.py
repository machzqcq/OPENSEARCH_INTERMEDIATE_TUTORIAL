#!/usr/bin/env python3
"""
Generate comprehensive course catalog with deep analysis of all files.
Creates OpenSearch-compatible JSONL format with extensive tags.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional

try:
    import nbformat
    HAS_NBFORMAT = True
except ImportError:
    HAS_NBFORMAT = False
    print("Warning: nbformat not installed. Notebook analysis will be limited.")

# Target folders to include
TARGET_FOLDERS = [
    "1. INSTALLATION_CONFIGURATION",
    "2. TRADITIONAL_SEARCH",
    "3. INGEST_AND_SEARCH_CONCEPTS",
    "4. AI_SEARCH",
    "5. AGENTIC_SEARCH",
    "6. REALTIME_PROJECTS"
]

# Files to include at root
ROOT_FILES = ["helpers.py"]

# Folders/patterns to exclude
EXCLUDE_PATTERNS = [".venv", "__pycache__", ".egg-info", "node_modules", ".git", ".ipynb_checkpoints"]

# Comprehensive tag extraction patterns
TAG_PATTERNS = {
    # OpenSearch/Elasticsearch concepts
    'opensearch_basics': [
        r'\bopensearch\b', r'\belasticsearch\b', r'\bindex\b', r'\bindices\b', r'\bmapping\b',
        r'\bsettings\b', r'\bshards\b', r'\breplicas\b', r'\bcluster\b', r'\bnodes\b'
    ],
    'search_types': [
        r'\bkeyword\s+search\b', r'\bfull.?text\s+search\b', r'\bsemantic\s+search\b',
        r'\bhybrid\s+search\b', r'\bvector\s+search\b', r'\bneural\s+search\b',
        r'\bfuzzy\s+search\b', r'\bphrase\s+search\b', r'\bwildcard\b', r'\bregex\s+search\b'
    ],
    'query_types': [
        r'\bmatch\s+query\b', r'\bmatch_all\b', r'\bmulti_match\b', r'\bterm\s+query\b',
        r'\bterms\s+query\b', r'\brange\s+query\b', r'\bbool\s+query\b', r'\bfilter\b',
        r'\bmust\b', r'\bshould\b', r'\bmust_not\b', r'\bquery_string\b', r'\bsimple_query_string\b'
    ],
    'scoring': [
        r'\bbm25\b', r'\btf.?idf\b', r'\bscoring\b', r'\brelevance\b', r'\bboost\b',
        r'\bfunction.?score\b', r'\bscript.?score\b', r'\bfield.?value.?factor\b'
    ],
    'text_analysis': [
        r'\banalyzer\b', r'\btokenizer\b', r'\btoken.?filter\b', r'\bchar.?filter\b',
        r'\bstandard\s+analyzer\b', r'\bwhitespace\b', r'\bn.?gram\b', r'\bedge.?ngram\b',
        r'\bstemmer\b', r'\bstop.?words\b', r'\bsynonyms\b', r'\blowercase\b', r'\basciifolding\b'
    ],
    'vectors_embeddings': [
        r'\bvector\b', r'\bembedding\b', r'\bknn\b', r'\bk.?nearest.?neighbor\b',
        r'\bdense\s+vector\b', r'\bsparse\s+vector\b', r'\bcosine\s+similarity\b',
        r'\bdot.?product\b', r'\beuclidean\b', r'\bhnsw\b', r'\bivf\b', r'\bfaiss\b',
        r'\bnmslib\b', r'\blucene\b'
    ],
    'ml_models': [
        r'\bsentence.?transformer\b', r'\bbert\b', r'\bdistilbert\b', r'\broberta\b',
        r'\bgpt\b', r'\bt5\b', r'\ball.?minilm\b', r'\bmsmarco\b', r'\bmpnet\b',
        r'\bonnx\b', r'\btorchscript\b', r'\bml.?commons\b', r'\bmodel\s+registry\b'
    ],
    'neural_sparse': [
        r'\bneural.?sparse\b', r'\bsplade\b', r'\bsparsity\b', r'\blearned.?sparse\b',
        r'\btoken.?expansion\b', r'\bquery.?expansion\b'
    ],
    'reranking': [
        r'\brerank\b', r'\bre.?rank\b', r'\bcross.?encoder\b', r'\breciprocal.?rank\b',
        r'\brrf\b', r'\bmaximal.?marginal.?relevance\b', r'\bmmr\b', r'\bdiversity\b'
    ],
    'pipelines': [
        r'\bingest\s+pipeline\b', r'\bsearch\s+pipeline\b', r'\bprocessor\b',
        r'\btext.?embedding\b', r'\bnormalization\b', r'\bfilter\s+processor\b',
        r'\bscript\s+processor\b', r'\bset\s+processor\b', r'\bremove\s+processor\b'
    ],
    'ingestion': [
        r'\bbulk\s+api\b', r'\bbulk\s+ingestion\b', r'\bdata.?prepper\b', r'\blogstash\b',
        r'\bfluentd\b', r'\botel\b', r'\bopentelemetry\b', r'\bstreaming\b',
        r'\bbatch\s+processing\b', r'\bhelpers\.bulk\b'
    ],
    'performance': [
        r'\boptimization\b', r'\bperformance\b', r'\bcompression\b', r'\bcaching\b',
        r'\bsegment\s+replication\b', r'\brefresh\s+interval\b', r'\btranslog\b',
        r'\bjvm\b', r'\bheap\b', r'\bthreading\b', r'\bbulk\s+size\b'
    ],
    'production': [
        r'\bsnapshot\b', r'\brestore\b', r'\bbackup\b', r'\breindex\b', r'\balias\b',
        r'\brollover\b', r'\bism\b', r'\bindex\s+state\s+management\b', r'\btemplate\b'
    ],
    'rag': [
        r'\brag\b', r'\bretrieval.?augmented.?generation\b', r'\bknowledge.?base\b',
        r'\bconversational\b', r'\bmemory\b', r'\bchat.?history\b', r'\bcontext\s+window\b'
    ],
    'agents': [
        r'\bagent\b', r'\btool\b', r'\bfunction.?calling\b', r'\breact\b', r'\bplan.?execute\b',
        r'\breflect\b', r'\bscratchpad\b', r'\breasoning\b', r'\bchain.?of.?thought\b'
    ],
    'llm_providers': [
        r'\bopenai\b', r'\banthropic\b', r'\bclaude\b', r'\bollama\b', r'\bdeepseek\b',
        r'\bgpt.?4\b', r'\bgpt.?3\.5\b', r'\bllama\b', r'\bmistral\b'
    ],
    'connectors': [
        r'\bconnector\b', r'\bexternal\s+model\b', r'\bhosted\s+model\b', r'\bapi\s+key\b',
        r'\bendpoint\b', r'\bremote\s+model\b'
    ],
    'mcp': [
        r'\bmcp\b', r'\bmodel\s+context\s+protocol\b', r'\bserver\b', r'\bclient\b',
        r'\btool\s+registry\b'
    ],
    'applications': [
        r'\bstreamlit\b', r'\bgradio\b', r'\bfastapi\b', r'\bflask\b', r'\bui\b',
        r'\bfrontend\b', r'\bbackend\b', r'\bapi\b', r'\brest\b'
    ],
    'databases': [
        r'\bmssql\b', r'\bpostgres\b', r'\bpostgresql\b', r'\bsql\s+server\b',
        r'\btext.?to.?sql\b', r'\bsql\s+query\b', r'\bmetadata\b'
    ],
    'visualization': [
        r'\bvisualization\b', r'\bplotly\b', r'\bmatplotlib\b', r'\bcharts\b',
        r'\bgraphs\b', r'\bdashboard\b', r'\bmetrics\b'
    ],
    'geospatial': [
        r'\bgeo.?spatial\b', r'\bgeo.?point\b', r'\bgeo.?shape\b', r'\bgeo.?distance\b',
        r'\blat.?lon\b', r'\blatitude\b', r'\blongitude\b', r'\bmap\b'
    ],
    'docker': [
        r'\bdocker\b', r'\bdocker.?compose\b', r'\bcontainer\b', r'\bimage\b',
        r'\bvolume\b', r'\bnetwork\b', r'\bCUDA\b'
    ],
    'security': [
        r'\bauth\b', r'\bauthentication\b', r'\bauthorization\b', r'\bsecurity\b',
        r'\bssl\b', r'\btls\b', r'\bcertificate\b', r'\bcredentials\b'
    ]
}

# Acronym mapping
ACRONYMS = {
    'bm25': 'Best Matching 25',
    'knn': 'k-Nearest Neighbors',
    'hnsw': 'Hierarchical Navigable Small World',
    'ivf': 'Inverted File Index',
    'rrf': 'Reciprocal Rank Fusion',
    'mmr': 'Maximal Marginal Relevance',
    'rag': 'Retrieval Augmented Generation',
    'llm': 'Large Language Model',
    'mcp': 'Model Context Protocol',
    'ism': 'Index State Management',
    'jvm': 'Java Virtual Machine',
    'otel': 'OpenTelemetry',
    'onnx': 'Open Neural Network Exchange',
    'ui': 'User Interface',
    'api': 'Application Programming Interface',
    'ssl': 'Secure Sockets Layer',
    'tls': 'Transport Layer Security',
    'sql': 'Structured Query Language',
    'rest': 'Representational State Transfer',
    'cuda': 'Compute Unified Device Architecture',
    'ml': 'Machine Learning',
    'ai': 'Artificial Intelligence',
    'qa': 'Question Answering',
    'nlp': 'Natural Language Processing',
    'dsl': 'Domain Specific Language',
    'ppl': 'Piped Processing Language'
}


class CourseFileCatalog:
    """Analyze and catalog course files with comprehensive tagging."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.catalog = []
        self.index_counter = 0
        
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)
    
    def extract_tags_from_text(self, text: str, filename: str) -> Set[str]:
        """Extract comprehensive tags from text content."""
        tags = set()
        text_lower = text.lower()
        
        # Extract tags based on patterns
        for category, patterns in TAG_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    # Add the category
                    tags.add(category.replace('_', ' '))
                    # Add specific matches
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    for match in matches[:5]:  # Limit to 5 per pattern
                        cleaned = match.strip().replace('_', ' ').replace('.', '')
                        if cleaned and len(cleaned) > 2:
                            tags.add(cleaned)
        
        # Add acronyms found in text
        for acronym, full_form in ACRONYMS.items():
            if re.search(r'\b' + acronym + r'\b', text_lower):
                tags.add(acronym.upper())
                tags.add(full_form.lower())
        
        # Extract from filename
        filename_tags = self.extract_filename_tags(filename)
        tags.update(filename_tags)
        
        # Add file type tags
        if filename.endswith('.py'):
            tags.add('python script')
            tags.add('implementation')
        elif filename.endswith('.ipynb'):
            tags.add('jupyter notebook')
            tags.add('interactive tutorial')
        elif filename.endswith('.md'):
            tags.add('documentation')
            tags.add('markdown')
        elif filename.endswith('.yml') or filename.endswith('.yaml'):
            tags.add('configuration')
            tags.add('docker compose')
        
        return tags
    
    def extract_filename_tags(self, filename: str) -> Set[str]:
        """Extract tags from filename."""
        tags = set()
        name = filename.lower().replace('_', ' ').replace('-', ' ').replace('.py', '').replace('.ipynb', '').replace('.md', '')
        
        # Split by common separators and add words
        words = re.split(r'[_\-\s\.]', name)
        for word in words:
            if len(word) > 2 and word.isalpha():
                tags.add(word)
        
        return tags
    
    def read_python_file(self, filepath: Path) -> str:
        """Read and extract content from Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract docstrings, comments, function names, class names
            elements = []
            elements.append(content)
            
            # Extract function and class names
            functions = re.findall(r'def\s+(\w+)', content)
            classes = re.findall(r'class\s+(\w+)', content)
            elements.extend(functions)
            elements.extend(classes)
            
            return ' '.join(elements)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def read_notebook_file(self, filepath: Path) -> tuple[str, Optional[str]]:
        """Read and extract content from Jupyter notebook, including embedded markdown."""
        try:
            if HAS_NBFORMAT:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    nb = nbformat.read(f, as_version=4)
                
                content_parts = []
                markdown_content = []
                
                for cell in nb.cells:
                    if cell.cell_type == 'code':
                        content_parts.append(cell.source)
                    elif cell.cell_type == 'markdown':
                        content_parts.append(cell.source)
                        markdown_content.append(cell.source)
                
                embedded_md = '\n\n'.join(markdown_content) if markdown_content else None
                return ' '.join(content_parts), embedded_md
            else:
                # Fallback: read as JSON
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    nb_data = json.load(f)
                
                content_parts = []
                markdown_content = []
                
                for cell in nb_data.get('cells', []):
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        source = ''.join(source)
                    
                    if cell.get('cell_type') == 'code':
                        content_parts.append(source)
                    elif cell.get('cell_type') == 'markdown':
                        content_parts.append(source)
                        markdown_content.append(source)
                
                embedded_md = '\n\n'.join(markdown_content) if markdown_content else None
                return ' '.join(content_parts), embedded_md
        except Exception as e:
            print(f"Error reading notebook {filepath}: {e}")
            return "", None
    
    def read_markdown_file(self, filepath: Path) -> str:
        """Read and extract content from Markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def read_yaml_file(self, filepath: Path) -> str:
        """Read and extract content from YAML file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return ""
    
    def find_associated_markdown(self, filepath: Path) -> Optional[str]:
        """Find associated markdown file for a given file."""
        # Check for same name with .md extension
        md_file = filepath.with_suffix('.md')
        if md_file.exists():
            return md_file.name
        
        # Check in docs subfolder
        docs_folder = filepath.parent / 'docs'
        if docs_folder.exists():
            doc_file = docs_folder / f"{filepath.stem}.md"
            if doc_file.exists():
                return f"docs/{doc_file.name}"
        
        # For notebooks, markdown is embedded
        if filepath.suffix == '.ipynb':
            return "embedded in notebook"
        
        return None
    
    def determine_module_submodule(self, filepath: Path) -> tuple[str, str]:
        """Determine module and submodule from file path."""
        parts = filepath.relative_to(self.base_path).parts
        
        # First part is module (e.g., "2. TRADITIONAL_SEARCH")
        module = parts[0] if len(parts) > 0 else "ROOT"
        
        # If there's a subfolder, that's the submodule
        if len(parts) > 2:
            submodule = parts[1]
        elif len(parts) == 2:
            submodule = ""
        else:
            submodule = ""
        
        return module, submodule
    
    def analyze_file(self, filepath: Path):
        """Analyze a single file and add to catalog."""
        if self.should_exclude(filepath):
            return
        
        print(f"Analyzing: {filepath.relative_to(self.base_path)}")
        
        module, submodule = self.determine_module_submodule(filepath)
        filename = filepath.name
        associated_md = self.find_associated_markdown(filepath)
        
        # Extract content and tags based on file type
        content = ""
        embedded_markdown = None
        
        if filepath.suffix == '.py':
            content = self.read_python_file(filepath)
        elif filepath.suffix == '.ipynb':
            content, embedded_markdown = self.read_notebook_file(filepath)
            if embedded_markdown and not associated_md:
                # Read the markdown content for tagging
                content += " " + embedded_markdown
        elif filepath.suffix == '.md':
            content = self.read_markdown_file(filepath)
        elif filepath.suffix in ['.yml', '.yaml']:
            content = self.read_yaml_file(filepath)
        elif filepath.suffix == '.dockerfile' or filepath.name.endswith('.dockerfile'):
            content = self.read_yaml_file(filepath)
        
        # Extract tags
        tags = list(self.extract_tags_from_text(content, filename))
        
        # Create catalog entry
        entry = {
            "module": module,
            "sub_module": submodule,
            "filename": filename,
            "associated_markdown_file": associated_md or "",
            "tags": tags,
            "file_path": str(filepath.relative_to(self.base_path)),
            "file_type": filepath.suffix[1:] if filepath.suffix else "unknown"
        }
        
        self.catalog.append(entry)
    
    def scan_directory(self, directory: Path):
        """Recursively scan directory for files."""
        if self.should_exclude(directory):
            return
        
        try:
            for item in directory.iterdir():
                if item.is_file():
                    # Include relevant file types
                    if item.suffix in ['.py', '.ipynb', '.md', '.yml', '.yaml'] or item.name.endswith('.dockerfile'):
                        self.analyze_file(item)
                elif item.is_dir():
                    self.scan_directory(item)
        except Exception as e:
            print(f"Error scanning {directory}: {e}")
    
    def generate_catalog(self):
        """Generate complete catalog for target folders and files."""
        print("Starting catalog generation...")
        
        # Process root files
        for root_file in ROOT_FILES:
            filepath = self.base_path / root_file
            if filepath.exists():
                self.analyze_file(filepath)
        
        # Process target folders
        for folder in TARGET_FOLDERS:
            folder_path = self.base_path / folder
            if folder_path.exists():
                print(f"\nScanning folder: {folder}")
                self.scan_directory(folder_path)
        
        print(f"\nCatalog generation complete. Total files: {len(self.catalog)}")
    
    def write_jsonl(self, output_file: str):
        """Write catalog to OpenSearch-compatible JSONL format."""
        print(f"\nWriting catalog to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, entry in enumerate(self.catalog):
                # Write index action
                index_action = {"index": {"_index": "course_catalog", "_id": idx}}
                f.write(json.dumps(index_action) + '\n')
                
                # Write document
                f.write(json.dumps(entry) + '\n')
        
        print(f"Successfully wrote {len(self.catalog)} entries to {output_file}")
        
        # Print statistics
        print("\n" + "="*60)
        print("CATALOG STATISTICS")
        print("="*60)
        print(f"Total files cataloged: {len(self.catalog)}")
        
        # Count by module
        module_counts = {}
        for entry in self.catalog:
            module = entry['module']
            module_counts[module] = module_counts.get(module, 0) + 1
        
        print("\nFiles per module:")
        for module, count in sorted(module_counts.items()):
            print(f"  {module}: {count}")
        
        # Count by file type
        type_counts = {}
        for entry in self.catalog:
            file_type = entry['file_type']
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        print("\nFiles by type:")
        for file_type, count in sorted(type_counts.items()):
            print(f"  {file_type}: {count}")
        
        # Tag statistics
        all_tags = []
        for entry in self.catalog:
            all_tags.extend(entry['tags'])
        
        print(f"Total unique tags: {len(set(all_tags))}")
        if len(self.catalog) > 0:
            print(f"Average tags per file: {len(all_tags) / len(self.catalog):.1f}")
        
        # Most common tags
        from collections import Counter
        tag_counts = Counter(all_tags)
        print("\nTop 20 most common tags:")
        for tag, count in tag_counts.most_common(20):
            print(f"  {tag}: {count}")


def main():
    """Main execution function."""
    base_path = "."
    output_file = "course_catalog_opensearch.jsonl"
    
    catalog = CourseFileCatalog(base_path)
    catalog.generate_catalog()
    catalog.write_jsonl(output_file)
    
    print("\n" + "="*60)
    print("CATALOG GENERATION COMPLETE!")
    print("="*60)
    print(f"Output file: {output_file}")
    print("\nYou can now ingest this into OpenSearch using:")
    print(f"  curl -X POST 'localhost:9200/_bulk' -H 'Content-Type: application/x-ndjson' --data-binary @{output_file}")


if __name__ == "__main__":
    main()
