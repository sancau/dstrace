import os
import sys

import fire
import git
import nbconflux
import yaml


DSTRACE_DEFAULT_COMMAND = 'dstrace'
DEFAULT_DSTRACE_CONFIG = {
    'confluence_api_username': None,
    'confluence_api_token': None,
    'confluence_pages': {},
}
DSTRACE_CONFIG_PATH = '.dstrace'
GIT_HOOKS_REL_PATH = '.git/hooks'
GIT_HOOK_PRE_COMMIT_PATH = os.path.join(GIT_HOOKS_REL_PATH, 'pre-commit')
GIT_HOOK_PRE_PUSH_PATH = os.path.join(GIT_HOOKS_REL_PATH, 'pre-commit')


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
        return f'{self.git_remote_url}/commit/{self.git_last_commit_hash}'

    @property
    def git_last_commit_message(self):
        return self.repo.head.commit.message

    def get_git_staged(self):
        return [i.a_path for i in self.repo.index.diff('HEAD')]

    def get_last_commit_changed_files(self):
        return self.repo.git.diff('HEAD~1..HEAD', name_only=True).split('\n')


class DSTrace:
    def __init__(self):
        if not os.path.exists(DSTRACE_CONFIG_PATH):
            self.config = DEFAULT_DSTRACE_CONFIG
            with open(DSTRACE_CONFIG_PATH, 'w') as f:
                f.write(yaml.dump(self.config))
        else:
            with open(DSTRACE_CONFIG_PATH) as f:
                self.config = yaml.load(f, Loader=yaml.SafeLoader)

        self.confluence_pages = self.config.get('confluence_pages', {})
        self.dvc_pipelines = self.config.get('dvc_pipelines', [])  # TODO

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

    def butch_publish_to_confluence(self):
        gp = GITProxy('.')
        pages_to_update = {
            notebook: confluence_url for notebook, confluence_url in self.confluence_pages.items()
            if notebook in gp.get_last_commit_changed_files()
        }
        if pages_to_update:
            count = len(pages_to_update)
            noun = 'page' if count == 1 else 'pages'
            sys.stdout.write(f'\nGoing to update {count} Confluence {noun}:\n')
            for i, (notebook, confluence_url) in enumerate(pages_to_update.items()):
                sys.stdout.write(f'{i + 1}. {notebook} >> {confluence_url}\n')
            sys.stdout.write('\n')

            username = self.config.get('confluence_api_username')
            if not username:
                username = input('Enter Confluence API username: ')
            token = self.config.get('confluence_api_token')
            if not username:
                token = input('Enter Confluence API token: ')
            
            for notebook, confluence_url in pages_to_update.items():
                self.publish_to_confluence(
                    source=notebook, 
                    target=confluence_url,
                    username=username,
                    token=token,
                )
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
        
        pre_commit = None
        while pre_commit not in ['y', 'n']:
            pre_commit = input(
                '\n[SETUP PRE-COMMIT BEHAVIOR]\n'
                f'{"=" * 40}\n'
                'Do you want to add pre-commit git hook?\n'
                'This will perform the operations listed below before each git commit:\n'
                '1. Convert all .ipynb files to .py using nbconvert to improve version control verbosity\n'
                '2. Add all of the converted .py representations to the commit.\n'
                'Enter either "y" or "n" and press Enter.\n',
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
                '1. Update Confluence pages for each changed Jupyter notebook that '
                'has a specified corresponding page URL in .dstrace\n'
                # TODO commit urls
                # '2. Add commit url to the top of all of the updated Confluence pages\n.'
                'Enter either "y" or "n" and press Enter.\n',
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
        dstrace.butch_publish_to_confluence()
        sys.stdout.write('\nDSTrace pre-push completed.\n\n')

    @staticmethod
    def convert_staged_notebooks():
        gp = GITProxy('.')
        to_convert = []
        for f in gp.get_git_staged():
            name, ext = os.path.splitext(f)
            if ext == '.ipynb' and os.path.exists(f):  # this may be a staged deletion:
                to_convert.append(f)
        if not to_convert:
            sys.stdout.write('Nothing to convert. HEAD contains no modified notebooks.\n')
        for f in to_convert:
            os.system(f'jupyter nbconvert --to script {f} --output {f} && git add {f}.py')


def main():
    fire.Fire(CLI)


if __name__ == '__main__':
    main()
