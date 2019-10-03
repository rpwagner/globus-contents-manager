# Useful Info
This document contains various useful information that doesn't fall in a particular category.

## Useful Links & GitHubRepos
Below are some links that I found useful while implementing the GlobusContentsManager and brief descriptions (including how I used them).

[General ContentsManager Info](https://jupyter-notebook.readthedocs.io/en/stable/extending/contents.html)
* Jupyter Notebook documentation that describes the ContentsManager and how to make a custom one.
* Good place to start, but doesn't go into very much detail

[AWS S3 ContentsManager](https://github.com/danielfrg/s3contents)
* Custom ContentsManager that uses AWS S3.
* Mostly used as a guide on what to implement.
* Used some of the code from this project, but gave proper credit in the top docstring of every relevant file.

[PostgreSQL ContentsManager](https://github.com/quantopian/pgcontents)
* Custome ContentsManager that uses PostgreSQL.
* Mostly used as a guide on what to implement; similar to S3ContentsManager, except that this ContentsManager was mostly used to ensure that only the aspects of the code shared by both PGContents and S3Contents, and therefore not dependent on the specific file system used, was implemented.

## Issues Encountered
Only the issues that might come up again are listed here. If you encounter additional issues or new solutions to existing issues, please create a new [Issue](https://github.com/gneezyn/globus-contents-manager/issues).

#### tornado & nbconvert
* Problem - when trying to run `jupyter notebook` (in the terminal) it is possible to get various errors that accummulate into the image below (the token mentioned in the image is NOT a Globus token):
![alt text](images/nbconvert_tornado_issue.png)
* Solution - there are two parts to the solution, although it is possible that only one part is needed to fix the issue
    * `nbconvert` - make sure that `nbconvert` is updated
        * Using pip: `pip install --upgrade --user nbconvert`
        * Using anaconda: `conda upgrade nbconvert`
    * `tornado` - make sure that the tornado version is less than 6
        * This part of the solution is addressed in the `requirements.txt` file so it is unlikely to be the cause of the problem
* Note: the root cause of this issue is not entirely clear, which means that the solutions stated above might not thoroughly address the issue.

## TODOs
Various functionalities that are still in the process of being implemented and properly tested.

#### Testing (with possible refactoring) Globus Functionality
* Currently the project is at a state where the GlobusContentsManager successfully runs in a Jupyter Notebook; however, much of the actual functionality (i.e., syncing with a Globus endpoint, making a new file/directory, etc.) is missing.
    * So far the main part of the code that has been confirmed as working is the Globus Login and Auth.
    * Most of the code has already been written; with testing, debugging, and refactoring the GlobusContentsManager should work properly.
* This TODO has a high priority as it deals with the main purpose of the GlobusContentsManager.

#### Converting Hard-Code to Config
* Currently, all of the user-dependent variables (i.e., client_id, endpoint_id, etc.) are hard-coded since getting the Globus functionalit working is a higher priority.
* Most of the variables can, and in most cases should, be specified through config. Below are some of the approaches that have been considered:
    * Jupyter Notebook Config - since users already need to edit the `jupyter_notebook_config.py` file, it makes sense to also specify any user-dependent variables in this file.
    * Other Config File - using a local file for config would let users easily switch between different configurations (i.e., switching between endpoints or Client IDs)
