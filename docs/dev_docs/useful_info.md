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
    * Problem - when trying to run **'jupyter notebook'** (in the terminal) it is possible to get various errors that accummulate into the image below (the token mentioned in the image is NOT a Globus token):
    ![](nbconvert_tornado_issue.png?raw=true)