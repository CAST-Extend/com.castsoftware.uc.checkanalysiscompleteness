# Unanalysed Code Report

Generates a report showing the **delivered source code that has not been analyzed**. 

It also provides the language of that missed code and recommendations.

## Features


This extension basically search for the code/config that is present in the delivery but not analyzed.
It serves to check that analysis is complete or not after analysis. 

The result is an excell report containing :
- the list of unanalyzed files per recognized language
- the list of unanalyzed language found and sometimes an associated recommendation

Due to the 'systematic' nature of this extension, the result still need human interpretation. 
Files that you have not selected 'on purpose' will still be presented here (unit tests, external code, etc...) 

The language list contains more than 200 different 'languages'.
 

## How it works

The CAST Knowledge Base contains the list of analyzed files, we compare this list to the files physically present in the deployment folder.

More precisely:

- detect the root path of code
- find the 'text' files that where not analyzed
  - filter some well known files that are not interesting (for example eclipse files, git, svn files...)
  - libmagic then tells us if a file is text or not
  - try to recognize the language of each text file using a database taken from https://github.com/liluo/linguist
  - generate a report 

All this is based on the CAST SDK and serves to demonstrate its possibilities.

## How to contribute


Contact m.roger@castsoftware.com.

Bugs and real analysis results are very welcome.
The top is to provide knowledge base dump + source code... 

You may also send a thank you if you find this useful.

## Changelog


- list all files paths, for debug  
- using https://github.com/faph/Common-Path for root discovery 
- adding a summary
- suggest Core analyser/UA/Extension

## Todos

- group xml per namespace/dtd...
- search for class fullnames in xml 

## Problems


- root detection
  - for example we miss ...
  - tryed deploy\app name but we take the external files in C++ !!
    - get_file + external ?
    - .h are useless and do not constitute the necessity to add an AU 
- unalaysed source
  - we point to tests whereas they have probably been excluded on purpose 
