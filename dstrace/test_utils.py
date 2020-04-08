import os


def save_tmp_file(tmp_path, path='tmp.ipynb',html=True):
   with open(tmp_path, 'r') as f:
       data = f.read()
   with open(path, 'w') as f:
       f.write(data)
   print('Wrote', tmp_path)
   if html:
       os.system(f'jupyter nbconvert --to html {path}')


def test_processor(raw_data: str) -> str:
    """A test processor for debug purposes.
    """
    nb = json.loads(raw_data)

    test_cell = {
        "cell_type": "markdown",
        "metadata": {
            "collapsed": True,
        },
        "source": [
            f"TEST STRING"
        ]
    }
    nb['cells'] = [test_cell] + nb['cells']
    return json.dumps(nb)

