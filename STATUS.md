Current status:  
  
Working on getting sphinx autodocumentation to work. Currently I'm having issues with apidoc not detecting and properly generating docs for my functions.  
  
Need to correct this and ultimately incorporate building the docs (and tests of the build?) into a github action CI process similar to https://youtu.be/kiUNFD6hcJM?feature=shared.  
  
Need to configure precommit with github actions to properly check the code.  
  
Progress:  
  Had first successful deployment to readthedocs website  
  Successfully published template package on pypi  
  Successfully configured pytest and nox   
  Established code structure   
  
Next:  
  Fix precommit  
  Write + get code working  
  Then revisit documentation issues  
    
Note:  
  Getting the .venv to work with vscode was a big challenge  
  Steps:  
    (1) create an ipykernel in the .venv - unclear what I did that made this work...
    (2) update the jupyter extension settings to add the path to the new kernel  
    Then it works (mostly)


#### 04/05/25  
Completed first implementation of planned functions.  
*TODO*  
* make bar plot more robust in terms of color cycles etc, especially for different categories (only 3 supported)
* add option to include uncategorized in plots to give an idea of rejection ratios (similar for number of items that were not processed bc no HTML or PDFS)
* reach out for help with the documentation
* work on real test case
* make sure that you can optionally turn down the logging levels
* ensure that the new category folders are created without spaces in the path