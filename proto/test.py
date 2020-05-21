#%%
import yaml

with open('proto/config.yaml') as f:
    data = yaml.load(f, Loader=yaml.SafeLoader)
with open('proto/configlocal.yaml') as f:
    local_data = yaml.load(f, Loader=yaml.SafeLoader)

data.update(local_data)

config = {'globals': {}, 'nodes': {}}

print('GLOBAL VARS')
print('=' * 40)
for key, value in data.items():
    if not isinstance(value, dict):
        print(f'{key}: {value}')
        config['globals'][key] = value

print('\nNODES CONFIG:')
for path, node_cfg in data['nodes'].items():
    print('=' * 40)
    print('Path:', path)
    config['nodes'][path] = {'scripts': {}}

    for script, ctx in node_cfg.items():
        print()
        print('Script name:', script)
        print('Script context:', ctx)
        script_body = data['scripts'][script]
        print('Script body:', script_body)
        print()
        config['nodes'][path]['scripts'][script] = {
            'body': script_body,
            'ctx': ctx,
        }
