#!/usr/bin/env python3
"""
Script to split files containing multiple Variable classes into separate files.
Each Variable class will be placed in its own file with a filename matching the class name.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple, Dict


def extract_imports_and_classes(content: str) -> Tuple[str, List[Dict[str, any]]]:
    """
    Extract imports section and Variable class definitions from file content.
    
    Returns:
        - imports: The import statements at the beginning of the file
        - classes: List of dicts with 'name', 'start_line', 'end_line', and 'content'
    """
    lines = content.split('\n')
    
    # Find where imports end (first line that starts with 'class' or is not import/comment/blank)
    import_end = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith(('import ', 'from ', '#', 'warnings')):
            if not stripped == '' and not 'import' in stripped:
                import_end = i
                break
    
    # Get imports section
    imports = '\n'.join(lines[:import_end]).strip()
    if imports and not imports.endswith('\n\n'):
        imports += '\n\n'
    
    # Find all Variable class definitions
    classes = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for class definition that inherits from Variable
        match = re.match(r'^class\s+(\w+)\s*\(\s*Variable\s*\)\s*:', line)
        if match:
            class_name = match.group(1)
            start_line = i
            
            # Find the end of the class by looking for the next class definition or end of file
            end_line = i + 1
            while end_line < len(lines):
                if re.match(r'^class\s+\w+', lines[end_line]):
                    # Found another class definition
                    break
                end_line += 1
            
            # Back up to remove trailing blank lines
            while end_line > start_line + 1 and not lines[end_line - 1].strip():
                end_line -= 1
            
            # Include the class definition
            class_content = '\n'.join(lines[start_line:end_line]).rstrip()
            
            classes.append({
                'name': class_name,
                'start_line': start_line,
                'end_line': end_line,
                'content': class_content
            })
            
            i = end_line - 1
        i += 1
    
    return imports, classes


def split_file(file_path: Path, dry_run: bool = False) -> int:
    """
    Split a file containing multiple Variable classes into separate files.
    
    Args:
        file_path: Path to the file to split
        dry_run: If True, only print what would be done without making changes
        
    Returns:
        Number of files created (or would be created in dry-run mode)
    """
    content = file_path.read_text()
    imports, classes = extract_imports_and_classes(content)
    
    if len(classes) <= 1:
        return 0
    
    print(f"\nProcessing {file_path}")
    print(f"  Found {len(classes)} Variable classes: {', '.join(c['name'] for c in classes)}")
    
    created_files = []
    files_to_create = []
    
    for class_info in classes:
        new_filename = f"{class_info['name']}.py"
        new_path = file_path.parent / new_filename
        
        # Check if file already exists
        if new_path.exists() and new_path != file_path:
            print(f"  WARNING: {new_path} already exists, skipping {class_info['name']}")
            continue
        
        # Create new file content
        new_content = imports + class_info['content'] + '\n'
        files_to_create.append((new_path, new_content))
        
        if dry_run:
            print(f"  Would create: {new_path}")
        else:
            new_path.write_text(new_content)
            print(f"  Created: {new_path}")
            created_files.append(new_path)
    
    if not dry_run and created_files:
        # Remove the original file
        file_path.unlink()
        print(f"  Removed original file: {file_path}")
    
    return len(files_to_create) if dry_run else len(created_files)


def find_multi_variable_files(root_dir: Path) -> List[Path]:
    """Find all Python files containing multiple Variable classes."""
    multi_var_files = []
    
    for py_file in root_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
            
        try:
            content = py_file.read_text()
            # Count Variable class definitions
            var_count = len(re.findall(r'^class\s+\w+\s*\(\s*Variable\s*\)\s*:', 
                                       content, re.MULTILINE))
            if var_count > 1:
                multi_var_files.append(py_file)
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return multi_var_files


def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Split files with multiple Variable classes')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--path', type=str, 
                       default='policyengine_uk/variables',
                       help='Path to variables directory (default: policyengine_uk/variables)')
    args = parser.parse_args()
    
    root_dir = Path(args.path)
    
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist")
        return 1
    
    print(f"Searching for files with multiple Variable classes in {root_dir}")
    multi_var_files = find_multi_variable_files(root_dir)
    
    if not multi_var_files:
        print("No files with multiple Variable classes found!")
        return 0
    
    print(f"\nFound {len(multi_var_files)} files with multiple Variable classes:")
    for f in multi_var_files:
        print(f"  {f}")
    
    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be made")
    
    total_created = 0
    for file_path in multi_var_files:
        created = split_file(file_path, dry_run=args.dry_run)
        total_created += created
    
    if not args.dry_run:
        print(f"\nSplit complete! Created {total_created} new files.")
    else:
        print(f"\nDry run complete. Would create {total_created} new files.")
    
    return 0


if __name__ == '__main__':
    exit(main())