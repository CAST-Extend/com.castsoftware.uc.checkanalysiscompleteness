# Unanalysed Code Report

Generates a report showing the **delivered source code that has not been analyzed** by 
comparing the Knowledge Base content to the deployment folder content. 

It also provides the language of that missed code and recommendations.

[Documentation](https://github.com/CAST-Extend/com.castsoftware.uc.checkanalysiscompleteness)

## Usage

- Install on a triplet
- Run the analysis
  
  - the report is generated during the CAST-MS step 
    
    'Run Extensions at application level for ...'

  - the report can be sent by email during analysis (new in 0.1.0)
    See : [Email to send report option](http://doc.castsoftware.com/display/DOC80/CMS+-+Notes+tab) 
    and [Mail server configuration](http://doc.castsoftware.com/display/DOC80/CMS+-+Preferences+-+Mail)
    
    If you get warnings like 'SMTP AUTH extension not supported by server' then try configuring without authentification.

  - the report path is indicated inside the Application Level log :
    
    Checking application completeness
    ...
    Found ... unanalyzed text files
    Generated report C:\Users\mro\AppData\Local\Temp\CAST\CAST\8.1\LISA\1a4ad8521e3a436db4ea149f2d49e6d1\completeness_report.xlsx
    
  - the report is named  *completeness_report.xlsx* and is located in the LISA folder of your application
  
![The log file containing the path](/report.png)


## Features

This extension basically search for the code/config that is present in the deploy but not analyzed.
It serves to check that analysis is complete or not **after analysis**. 

The result is an excel report containing :
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
  - [libmagic](https://en.wikipedia.org/wiki/File_(command)) then tells us if a file is text or not
  - try to recognize the language of each text file using a database taken from https://github.com/liluo/linguist
  - generate a report 

All this is based on the CAST SDK and serves to demonstrate its possibilities.

## How to contribute

For bugs, feature requests 
- create a ticket [here](https://github.com/CAST-Extend/com.castsoftware.uc.checkanalysiscompleteness/issues) 
- for bugs provide :
  - Application Level log
  - generated report 

For contributions 
- create a pull request [here](https://github.com/CAST-Extend/com.castsoftware.uc.checkanalysiscompleteness/pulls) 

Contact m.roger@castsoftware.com.

You may also send a thank you if you find this useful.

## Changelog

- list all files paths, for debug  
- using https://github.com/faph/Common-Path for root discovery 
- adding a summary
- suggest Core analyser/UA/Extension

0.1.0
- corrects percentage formula
- corrects false root folder path due to files from jars (tld)
- in case of combined install only :
  - send the report by email if option is configured
  - get the application root pathes from mngt   

0.1.3

- add the CMS package name when available
- correct '/' in report path
- add a Debug sheet in report
    - CAIP version
    - plugins version
    - root pathes found
    - heuristic used
    - limit reached 
- corrects a bug due to xls crashing magic (skipping those files)
- use latest api to avoid external file issue 
    
## Todos

- search for class fullnames in xml 
- have error message of file.exe somewhere...
- group xml per namespace/dtd...

## Problems

- root detection when cannot find managment base
- unalaysed source
  - we point to tests whereas they have probably been excluded on purpose 

  
  