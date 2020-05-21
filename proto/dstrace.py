"""
In one sentence
===============
DSTrace is the CI/CD for your Jupyter notebooks as well as Markdown/Sphinx documentation.
It built to play best with Confluence, but can be customized to any specific needs.

What is DSTrace?
================
DSTrace is a configuration and exporting framework mostly centered on Jupyter notebook formats
and Confluence interaction.
It uses Git Hooks concept to provide automation on commit and push actions.

Configuration Concepts
======================
Main configuration file is dstrace.yaml that is placed in the projects (and .git) root.
It is also possible to create dstracelocal.yaml file that can host Confluence credentials and
other configuration that SHOULD NOT be versioned with Git (so dstracelocal.yaml must be added
to .gitignore)
"""

def export_markdown(self, data: str) -> str:
    """Knows how to export a markdown file contents given as string to a Confluence API payload string.
    """
    raise NotImplementedError

def export_jupyter_notebook(self, data: str, *, code: bool, commit_url: bool) -> str:
    """Knows how to export a Jupyter Notebook file contents given as string to a Confluence API payload string.
    """
    raise NotImplementedError


class GitProxy:
    """Knows how to interact with a GIT repository.
    """
    def __init__(self, repository_root_path: str):
        self.repository_root_path = repository_root_path


class DSTraceConfig:
    """This is what the DSTrace configuration is.
    Knows how to read the configuration file and how to validate it.
    Provides access to configuration for the DSTrace business logic code.
    """
    @classmethod
    def from_file(cls, path: str) -> 'DSTraceConfig':
        return cls()

    @classmethod
    def merge_configs(cls, *configs_priority_sorted) -> 'DSTraceConfig':
        """Merges arbitrary number of DSTrace configurations.
        Priority is from left to right (right will overwrite members from the left)
        """
        return cls()


class DSTrace:
    """The business logic of the package.
    """
    def __init__(self, *, config_path: str, local_config_path: str = None, git_root_path: str = None):
        self.config = DSTraceConfig.from_file(config_path)
        if local_config_path:
            local_config = DSTraceConfig.from_file(local_config_path)
            self.config = DSTraceConfig.merge_configs(self.config, local_config)
        self.git = None
        if git_root_path is not None:
            self.git = GitProxy(git_root_path)

    def convert(self, *, config_node):
        raise NotImplementedError

    def upload(self, *, config_node):
        raise NotImplementedError

    def notify(self, *, config_node):
        raise NotImplementedError

