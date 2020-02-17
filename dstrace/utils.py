import json
import os
import uuid


def remove_inputs(path):
    """Returns JSON-formatted notebook (sourced from <path>) with removed code.
    """
    with open(path) as f:
        nb = json.loads(f.read())
    clean_cells = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if not cell['outputs']:
                continue
            cell['source'] = ['# code hidden...']
        clean_cells.append(cell)
    nb['cells'] = clean_cells
    return json.dumps(nb)


def with_processed_temp_file(processor):
    """Applies <processor> to the file on the given path.
    Passes processed temp file path to the decorated function.
    After the decorated function finishes it's job - removes the temp processed file.
    """
    def deco(func):
        def inner(path):
            processed_data = processor(path)
            temp_file_path = str(uuid.uuid4())
            with open(temp_file_path, 'w') as f:
                f.write(processed_data)
            result = func(temp_file_path)
            os.remove(temp_file_path)
            return result
        return inner
    return deco
