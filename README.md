# zbinfigs

## Overview
zbinfigs is a python code designed to facilitate classification of scholarly articles stored in zotero collecctions. 
The code input is a .csv exported from a zotero collection. The code allows for several options:  
  1. Organize and compile .pdfs
  2. Extract images to summary .pdf
  3. Read annotations
  4. Train and test classifier

### Organize and Compile
A raw zotero collection may not have .pdf files for all records, and for those that have .pdf files not all may be acessible. 
In the organize and compile option, the program reads a default .csv describing a zotero collection and checks all of the file links.
Where no files are available, this flag is written to a summary document. If only .html files are available, the program strips the CSS 
from the file and converts it to a .pdf file. At the end of the program execution, all available .pdf files are written to a common folder. 
This can be useful to transfer data to an HPC system for further analysis.  

### Extract Images 
From a folder of .pdf files and the orginal exported zotero .csv file, the program uses the **marker** package to convert to markdown and 
extract the figure images. The figure images for the entire directory are stitched into a single .pdf file for review and annotation. 
The converted text and original image files are retainedd for further semantic analysis. This step may be broken into chunks for parallel processing 
on an HPC system.

### Read Annotations 
The program takes an annotations input file that contains the .pdf page number for all figures that match from manual annotation. 
These annotations are then connected with the original zotero collection .csv file and summary stats written.  

### Train and Test Clasifier  
From the annotated dataset, several classifiers are applied and summary performance written.  
