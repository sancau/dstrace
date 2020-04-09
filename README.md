# DSTrace is a data science workflow helper

- More comprehensive documentation to come. The project is currently at an early stage. We are using this at [Welltory](https://welltory.com) data science team and find it helpful. But still there is much of work to do until the tool is stable and has clear enough documentation.

- If you find the idea useful but have problems using the tool - feel free to post an issue. I'll be glad to help you out.

- Being an experiment at an early stage, the tool probably have bugs and WTFs here and there. Once again, please post issues if you'll find something.

## TLDR

### What it does?

DSTrace is trying to solve two common problems:

1. Make VCS history for Jupyter notebooks meaningful and manageable
2. For those who use Confluence to share their results DSTrace will help to keep Jupyter notebooks in sync with corresponding Confluence pages

### How it does that?

- DSTrace is using GIT hooks to perform some operations on every commit and on every push
- If a notebook was changed DSTrace will use Jupyter's *nbconvert* to built a Python representation of that notebook and will automatically add it to the commit

*You now have a meaningful git diff :)*

- DSTrace will help to synchronize changed notebooks with their corresponding Confluence pages that can be configured in a DSTrace config file (that is also goes to VCS)

*You now have Confluence documentation synchronized with the actual research in Jupyter. And there's more. You also have each Confluence page version bind to a specific GIT commit :)*

##### NOTE

Currently the tool uses [NbConflux](https://github.com/Valassis-Digital-Media/nbconflux.git) to interact with Confluence.
\
Unfortunately NbConflux seem not to be active anymore.
\
For now I've chosen vedoring strategy to be able modify nbconflux here and there without the need to fork it and support an another package.
\
This is not very clean approach but it does the job and allows to iterate faster.

## Step by step example

#### 1. Create a GIT repo or use an existing one

**Let's assume you have your repo in */home/user/repo/* and that the repo has a Jupyter notebook *test_notebook.ipynb* in it**

#### 2. `pip install -U dstrace`
#### 3. `cd /home/user/repo`
#### 4. `dstrace init`

DSTrace will ask you some questions. After that it will add appropriate GIT hooks and will also create a configuration file

```shell
Initializing DSTrace in the current GIT repository.

[CURRENT CONFIGURATION]:

confluence_api_token: null
confluence_api_username: null
confluence_pages: {}
dstrace_command: dstrace


[SETUP PRE-COMMIT BEHAVIOR]
========================================
Do you want to add pre-commit git hook?
This will perform the operations listed below before each git commit:
1. Convert all .ipynb files to .py using nbconvert to improve version control verbosity
2. Add all of the converted .py representations to the commit.
Type either "y" or "n" and press Enter.
y

[SETUP PRE-PUSH BEHAVIOR]
========================================
Do you want to add pre-push git hook?
This will perform the operations listed below before each git push:
1. Update the corresponding Confluence page for each changed Jupyter notebook according to the configuration defined in .dstrace file.
2. Add the source commit URL to the top of every updated Confluence page.
Type either "y" or "n" and press Enter.
y

DSTrace configuration completed.
```

#### 5. `Create a Confluence page that will host our test_notebook.ipynb`

**Confluence pages must be created manually. Once you have a page just copy it's URL to clipboard**

#### 6. `Now let's configure DSTrace`

```yaml
confluence_pages:
  test_notebook.ipynb:
    branch: master
    confluence_url: <CREATED_CONFLUENCE_PAGE_URL>
    code: false
    no_commit_url: false
    no_conversion_to_python: false
```

#### 7. `Ensure a repo has initial commit (TEMP step, a bug to fix :))`

You also have to make any initial commit if the repo is empty: this is a DSTrace limitation (it can't work with clear new repo, going to fix it soon)

```shell
echo "DSTrace test" > README.md
git add README.md
git commit -m "Initial commit" --no-verify
```


#### 8. `Let's commit the changes`

```shell
(dstrace) mf% git status
On branch master
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   test_notebook.ipynb

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.dstrace
	.gitignore

no changes added to commit (use "git add" and/or "git commit -a")
(dstrace) mf% git add --all
(dstrace) mf% git commit -m "DSTrace test."
Calling DSTrace pre-commit hook

DSTrace pre-commit started.
[NbConvertApp] Converting notebook test_notebook.ipynb to script
[NbConvertApp] Writing 4700 bytes to test_notebook.ipynb.py

DSTrace pre-commit completed.

[master d6127cb] DSTrace test.
 4 files changed, 215 insertions(+), 1 deletion(-)
 create mode 100644 .dstrace
 create mode 100644 .gitignore
 create mode 100644 test_notebook.ipynb.py
```

You can see that DSTrace made a .py version of the notebook and automatically added it to the commit.

#### 9. `Now let's push the changes to the remote`

```
DSTrace pre-push started.

Going to update 1 Confluence page:
1. test_notebook.ipynb >> {'branch': 'master', 'confluence_url': <CREATED_CONFLUENCE_PAGE_URL>, 'code': False, 'no_commit_url': False, 'no_conversion_to_python': False}

Updated <CREATED_CONFLUENCE_PAGE_URL>

DSTrace pre-push completed.
```

During pre-push you will be prompted for Confluence API username and password.
It's also possible to create .dstracelocal file near the .dstrace config file with contents:

```
confluence_api_token: <YOUR_CONFLUENCE_API_KEY>
confluence_api_username: <YOUR_CONFLUENCE_USERNAME>
```

If .dstracelocal exists then DSTrace will try to use the credentials from the file.
Of course .dstracelocal SHOULD NOT go to VSC. To ensure that DSTrace will add it to .gitgnore during `dstrace init`


## Project status

The project is being actively (kinda :)) developed. The ongoing changes can be
monitored via CHANGES.md
