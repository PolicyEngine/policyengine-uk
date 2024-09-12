import os
import yaml
import nbformat
import nbconvert
import json
import time

def convert_notebook_to_json(notebook_path, output_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
        
        ep = nbconvert.preprocessors.ExecutePreprocessor(timeout=600, kernel_name='python3')
        start_time = time.time() 
        try:
            ep.preprocess(nb, {'metadata': {'path': os.path.dirname(notebook_path)}})
        except nbconvert.preprocessors.CellExecutionError as e:
            print(f"Error executing the notebook '{notebook_path}': {e}")
            return
        end_time = time.time() 

        elapsed_time = end_time - start_time
        print(f"Execution time for '{notebook_path}': {elapsed_time:.2f} seconds")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(nb, out_f, indent=2)

def process_toc(toc_file, base_dir, output_dir):
    with open(toc_file, 'r') as file:
        toc = yaml.safe_load(file)
    
    for part in toc.get('parts', []):
        for chapter in part.get('chapters', []):
            file_path = chapter['file']
            notebook_path = os.path.join(base_dir, f"{file_path}.ipynb")
            output_path = os.path.join(output_dir, f"{file_path}.json")
            if os.path.exists(notebook_path):
                convert_notebook_to_json(notebook_path, output_path)
            else:
                print(f"Notebook not found: {notebook_path}")

if __name__ == "__main__":
    curr_path = os.path.dirname(os.path.realpath(__file__))
    desired_path = os.path.dirname(os.path.dirname(curr_path))
    base_dir = os.path.join(desired_path, "docs/book")
    output_dir = os.path.join(desired_path, "docs/book/_build/json")
    toc_file = os.path.join(base_dir, "_toc.yml")
    print(base_dir, output_dir, toc_file)
    process_toc(toc_file, base_dir, output_dir)