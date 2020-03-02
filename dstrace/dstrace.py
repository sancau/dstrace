import json
import os
import uuid
import sys

import fire
import git
import nbconflux
import yaml


DSTRACE_DEFAULT_COMMAND = 'dstrace'
DSTRACE_DEFAULT_CONFIG = {
    'confluence_pages': {},
}
DSTRACE_DEFAULT_LOCAL_CONFIG = {
    'confluence_api_username': None,
    'confluence_api_token': None,
    'dstrace_command': DSTRACE_DEFAULT_COMMAND
}
DSTRACE_CONFIG_PATH = '.dstrace'
DSTRACE_LOCAL_CONFIG_PATH = '.dstracelocal'
GIT_HOOKS_REL_PATH = '.git/hooks'
GIT_HOOK_PRE_COMMIT_PATH = os.path.join(GIT_HOOKS_REL_PATH, 'pre-commit')
GIT_HOOK_PRE_PUSH_PATH = os.path.join(GIT_HOOKS_REL_PATH, 'pre-commit')


def add_remove_input_tags(raw_data: str) -> str:
    """Returns JSON-formatted notebook (sourced from <path>) with specific tags added.

    Accepts and returns raw data (utf-8 string).
    """
    nb = json.loads(raw_data)
    clean_cells = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if not cell['outputs']:
                continue
            # add tags that can be interpreted by nbconflux
            # look here for details:
            # https://github.com/Valassis-Digital-Media/nbconflux/blob/master/nbconflux/exporter.py#L71
            cell['metadata']['tags'] = ['noinput']
        clean_cells.append(cell)
    nb['cells'] = clean_cells
    return json.dumps(nb)


def add_commit_url(raw_data: str) -> str:
    """Adds commit url to the top of the notebook.

    Accepts and returns raw data (utf-8 string).
    """
    nb = json.loads(raw_data)

    gp = GITProxy('.')
    url = gp.git_last_commit_url
    url_cell = {
        "cell_type": "markdown",
        "metadata": {
            "collapsed": True,
        },
        "source": [
            f"Source commit: [{url}]({url})"
        ]
    }
    nb['cells'] = [url_cell] + nb['cells']
    return json.dumps(nb)


def with_preprocessed_temp_file(processors):
    """Applies each <processor> from <processors> to the file on the given path.
    Passes resulting processed temp file path to the decorated function.
    After the decorated function finishes it's job - removes the temp processed file.
    """
    def deco(func):
        def inner(path):
            temp_file_path = str(uuid.uuid4())
            try:
                with open(path) as f:
                    data = f.read()
                for processor in processors:
                    data = processor(data)
                with open(temp_file_path, 'w') as f:
                    f.write(data)
                return func(temp_file_path)
            except Exception as e:
                raise e
            finally:
                os.remove(temp_file_path)
        return inner
    return deco


class GITProxy:
    def __init__(self, path):
        self.path = path
        self.repo = git.Repo(path)

    @property
    def git_remote_url(self):
        remote_urls = list(self.repo.remote().urls)
        assert len(remote_urls) == 1, 'Multiple remotes are not supported.'
        return remote_urls[0].replace('.git', '')

    @property
    def git_last_commit_hash(self):
        return self.repo.head.commit.hexsha

    @property
    def git_last_commit_url(self):
        url = f'{self.git_remote_url}/commit/{self.git_last_commit_hash}'
        # cast to http format in case if origin is ssh based
        if 'git@' in url:
            return url.replace(':', '/').replace('git@', 'https://')
        return url

    @property
    def git_last_commit_message(self):
        return self.repo.head.commit.message

    def get_git_staged(self):
        return [i.a_path for i in self.repo.index.diff('HEAD')]

    def get_last_commit_changed_files(self):
        return self.repo.git.diff('HEAD~1..HEAD', name_only=True).split('\n')

    def get_changed_files_since_last_push(self):
        return self.repo.git.diff(f'origin/{self.repo.active_branch.name}', name_only=True).split('\n')


class DSTrace:
    def __init__(self):
        # load or create local config
        local_config = DSTRACE_DEFAULT_LOCAL_CONFIG
        if os.path.exists(DSTRACE_LOCAL_CONFIG_PATH):
            with open(DSTRACE_LOCAL_CONFIG_PATH) as f:
                local_config = yaml.load(f, Loader=yaml.SafeLoader)
        else:
            with open(DSTRACE_LOCAL_CONFIG_PATH, 'w') as f:
                f.write(yaml.dump(local_config))

        # load or create git aware config
        self.config = DSTRACE_DEFAULT_CONFIG
        if not os.path.exists(DSTRACE_CONFIG_PATH):
            with open(DSTRACE_CONFIG_PATH, 'w') as f:
                f.write(yaml.dump(self.config))
        else:
            with open(DSTRACE_CONFIG_PATH) as f:
                self.config = yaml.load(f, Loader=yaml.SafeLoader)

        # merge local config into VCS-aware config
        self.config.update(local_config)
        self.confluence_pages = self.config.get('confluence_pages', {})

    def add_git_hook(self, *, path, dstrace_handler_name, alias):
        existed_hook = None
        if os.path.exists(path):
            with open(path) as f:
                existed_hook = f.read()
                if all([
                    'DSTrace begin' in existed_hook,
                    'DSTrace end' in existed_hook,
                ]):
                    raise ValueError(
                        f'DSTrace {alias} hook already exists in this repository.\n'
                        'Aborting initialization to avoid breaking the current configuration.\n'
                        'If you really want to re-initialize DSTrace in this repository then manual steps are '
                        'required.\n'
                        f'Either remove existing {alias} git hook or remove DSTrace-created '
                        f'parts of the existing {alias} git hook and rerun "dstrace init" command.\n'
                    )

        dstrace_command = self.config.get('dstrace_command', DSTRACE_DEFAULT_COMMAND)
        with open(path, 'w') as f:
            content = (
                "\n\n" if existed_hook else ""
                "#[DSTrace begin]\n\n"
                "#!/bin/sh\n\n"
                f"echo 'Calling DSTrace {alias} hook'\n"
                f"exec {dstrace_command} {dstrace_handler_name}\n\n"
                "#[DSTrace end]\n"
            )
            f.write(content)

        # grant execution permissions
        os.system(f'chmod +x {path}')

    def set_pre_commit(self):
        self.add_git_hook(
            path='.git/hooks/pre-commit',
            alias='pre-commit',
            dstrace_handler_name='pre_commit',
        )

    def set_pre_push(self):
        self.add_git_hook(
            path='.git/hooks/pre-push',
            alias='pre-push',
            dstrace_handler_name='pre_push',
        )

    @staticmethod
    def publish_to_confluence(*, source: str, target: str, username: str, token: str):
        _, _ = nbconflux.notebook_to_page(
            source,
            target,
            username=username,
            password=token,
        )

    def get_pages_to_update(self):
        gp = GITProxy('.')

        return {
            notebook: confluence_config for notebook, confluence_config in self.confluence_pages.items()
            if
            notebook in gp.get_changed_files_since_last_push()
            and
            confluence_config['branch'] == gp.repo.active_branch.name
        }

    def batch_publish_to_confluence(self, pages):
        if pages:
            count = len(pages)
            noun = 'page' if count == 1 else 'pages'
            sys.stdout.write(f'\nGoing to update {count} Confluence {noun}:\n')
            for i, (notebook, confluence_config) in enumerate(pages.items()):
                sys.stdout.write(f'{i + 1}. {notebook} >> {confluence_config}\n')
            sys.stdout.write('\n')

            username = self.config.get('confluence_api_username')
            if not username:
                username = input('Enter Confluence API username: ')
            token = self.config.get('confluence_api_token')
            if not token:
                token = input('Enter Confluence API token: ')

            for notebook, confluence_config in pages.items():

                def do_publish(nb_path):
                    self.publish_to_confluence(
                        source=nb_path,
                        target=confluence_config['confluence_url'],
                        username=username,
                        token=token,
                    )

                processors = [
                    add_commit_url,
                ]
                if not confluence_config.get('code'):
                    processors.append(add_remove_input_tags)

                publish = with_preprocessed_temp_file(processors)(do_publish)
                publish(notebook)
        else:
            sys.stdout.write('No Confluence pages to update.\n')


class CLI:
    @staticmethod
    def init():
        sys.stdout.write('\nInitializing DSTrace in the current GIT repository.\n\n')
        dstrace = DSTrace()
        sys.stdout.write('[CURRENT CONFIGURATION]:\n\n')
        sys.stdout.write(yaml.dump(dstrace.config))
        sys.stdout.write('\n')

        # handle .gitignore
        # local configuration should not be in the VCS
        gitignore_path = '.gitignore'
        gitignore_string = f'\n\n# DSTrace\n{DSTRACE_LOCAL_CONFIG_PATH}\n\n'
        if os.path.exists(gitignore_path):
            with open(gitignore_path) as f:
                current = f.read().split('\n')
            with open(gitignore_path, 'a') as f:
                if DSTRACE_LOCAL_CONFIG_PATH not in current:
                    f.write(gitignore_string)
        else:
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_string)

        pre_commit = None
        while pre_commit not in ['y', 'n']:
            pre_commit = input(
                '\n[SETUP PRE-COMMIT BEHAVIOR]\n'
                f'{"=" * 40}\n'
                'Do you want to add pre-commit git hook?\n'
                'This will perform the operations listed below before each git commit:\n'
                '1. Convert all .ipynb files to .py using nbconvert to improve version control verbosity\n'
                '2. Add all of the converted .py representations to the commit.\n'
                'Type either "y" or "n" and press Enter.\n',
            ).lower()
        if pre_commit == 'y':
            dstrace.set_pre_commit()

        pre_push = None
        while pre_push not in ['y', 'n']:
            pre_push = input(
                '\n[SETUP PRE-PUSH BEHAVIOR]\n'
                f'{"=" * 40}\n'
                'Do you want to add pre-push git hook?\n'
                'This will perform the operations listed below before each git push:\n'
                '1. Update the corresponding Confluence page for each changed Jupyter notebook '
                'according to the configuration defined in .dstrace file.\n'
                '2. Add the source commit URL to the top of every updated Confluence page.\n'
                'Type either "y" or "n" and press Enter.\n',
            ).lower()
        if pre_push == 'y':
            dstrace.set_pre_push()

        sys.stdout.write('\nDSTrace configuration completed.\n')

    def pre_commit(self):
        sys.stdout.write('\nDSTrace pre-commit started.\n')
        self.convert_staged_notebooks()
        sys.stdout.write('\nDSTrace pre-commit completed.\n\n')

    @staticmethod
    def pre_push():
        sys.stdout.write('\nDSTrace pre-push started.\n')
        dstrace = DSTrace()
        dstrace.batch_publish_to_confluence(
            dstrace.get_pages_to_update(),
        )
        sys.stdout.write('\nDSTrace pre-push completed.\n\n')

    @staticmethod
    def convert_staged_notebooks():
        gp = GITProxy('.')
        to_convert = []
        for f in gp.get_git_staged():
            f = os.path.join(gp.repo.working_dir, f)  # absolute path
            name, ext = os.path.splitext(f)
            if ext == '.ipynb' and os.path.exists(f):  # this may be a staged deletion:
                to_convert.append(f)
        if not to_convert:
            sys.stdout.write('Nothing to convert. HEAD contains no modified notebooks.\n')
        for f in to_convert:
            os.system(f'jupyter nbconvert --to script {f} --output {f} && git add {f}.py')

    @staticmethod
    def force_update_confluence_pages():
        gp = GITProxy('.')
        dstrace = DSTrace()
        pages = {
            nb: config
            for nb, config in dstrace.confluence_pages.items()
            if config['branch'] == gp.repo.active_branch.name
        }
        dstrace.batch_publish_to_confluence(pages)


def main():
    fire.Fire(CLI)


if __name__ == '__main__':
    main()
