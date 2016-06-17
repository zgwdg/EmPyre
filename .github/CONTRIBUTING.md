# How To Contribute

Contributions are more than welcome! The more people who contribute to the project the better EmPyre will be for everyone. Below are a few guidelines for submitting contributions.


## Creating Github Issues

Please first review the existing EmPyre issues to see if the error was resolved with a fix in the development branch or if we chose not to fix the error for some reason.

The more information you provide in a Github issue the easier it will be for us to track down and fix the problem:

* Please provide the version of EmPyre you are using.
* Please provide the OS and Python versions that you are using.
* Please describe the expected behavior and the encountered error.
  * The more detail the better!
  * Include any actions taken just prior to the error.
  * Please post a screenshot of the error, a link to a Pastebin dump of the error, or embedded text of the error.
* Any additional information.


## Submitting Modules

* Submit pull requests to the [dev branch](https://github.com/adaptivethreat/EmPyre/tree/dev). After testing, changes will be merged to master.
* Base modules on the template at [./modules/template.py](https://github.com/adaptivethreat/EmPyre/blob/dev/lib/modules/template.py).
* Cite previous work in the **'Comments'** module section.
* If your script.py logic is large, may be reused by multiple modules, or is updated often, consider implementing the logic in the appropriate **data/module_source/*** directory and pulling the script contents into the module on tasking.
* TEST YOUR MODULE! Be sure to run it from an EmPyre agent before submitting a pull to ensure everything is working correctly.
* PEP8 is desired but not required.
