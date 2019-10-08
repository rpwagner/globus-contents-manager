# GlobusContentsManager (WIP)
A Globus backed ContentsManager implementation for Jupyter Notebook.

## Prerequisites
* An app registered with Globus. See the [Globus Auth Developer Guide](https://docs.globus.org/api/auth/developer-guide/) if you are unfamiliar with the Globus app registration process.
* The project's default settings uses the Globus Tutorial Endpoints, so you must be a member of the [Tutorial Users Group](https://app.globus.org/groups/50b6a29c-63ac-11e4-8062-22000ab68755)

## Installation
**Note**: At this time, the project must be installed locally.

#### Clone the repo
`$ git clone https://github.com/gneezyn/globus-contents-manager.git`

#### Install the GlobusContentsManager
`$ pip install globus-contents-manager`

#### Edit `~/.jupyter/jupyter_notebook_config.py`
* The `jupyter_notebook_config.py` file located in the root directory of this project provides an example of what the basic setup for this project would look like.
* This step is needed so that Jupyter knows to use the GlobusContentsManager instead of the default ContentsManager.
* If you do not have an existing `~/.jupyter/jupyter_notebook_config.py` file then you can either generate one or copy and paste the one provided in this project's root directory to the `~/.jupyter/` directory.
    * To generate a `jupyter_notebook_config.py` file, with all of the defaults commented out, run the following command: `$ jupyter notebook --generate-config`
    * You can refer to the [Jupyter Config Documentation](https://jupyter-notebook.readthedocs.io/en/stable/config.html) for more details on the different options (not including the ones specific to the GlobusContentsManager) available.

