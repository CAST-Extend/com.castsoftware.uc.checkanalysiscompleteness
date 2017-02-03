'''
Created on 23 déc. 2015

Take an application and add a worksheet to an excell for unanalyzed files

@todo : add also existing analyzer for some languages (name and url)

@todo : what to do with project files ? pom, .eclipse, .csproj etc...


@author: MRO
'''
import os, re, logging
import math
from sortedcontainers import SortedDict, SortedSet
from pathlib import PureWindowsPath
from magic import run_magic
from linguist import recognise_language
from commonpath import CommonPath


def generate_report(application, workbook):
    """
    Generate a worksheet report for files not analyzed in application
    """
    
    app = Application(application)
    return app.generate_report(workbook)



class Application:
    """
    Application discovery for users.
    
    
    """
    
    def __init__(self, application):
        
        self.languages = SortedDict()
        
        self.application = application
        
        # first calculate root path
        self.root_path = self.__get_root_path()
        
        # then get all the analysed files
        self.analyzed_files = self.__get_analysed_file_pathes()
         
        # then scan folder to find the files that where not taken into account
        self.unanalyzed_files = self.__get_unanalysed_files()
         
         
        self.languages_with_unanalysed_files = SortedSet()
        self.unanalysed_files_per_languages = SortedDict()
         
        # get the missing languages
        self.__get_languages()
    
    def generate_report(self, workbook):
        """
        Generate a worksheet report for files not analyzed in application
        """
        
        # summary
        percentage = self.summary(workbook)
        
        # for debug 
        self.list_files(workbook)
        
        # un analysed files per language
        self.list_unanalysed(workbook)
        
        return percentage
    
    def summary(self, workbook):
        
        worksheet = workbook.add_worksheet('Summary')
    
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 50)
        worksheet.set_column(3, 3, 50)
            
        worksheet.write(0, 0, 'Analyzed files count')
        worksheet.write(0, 1, len(self.analyzed_files))
        
        worksheet.write(1, 0, 'Unanalyzed files count')
        worksheet.write(1, 1, len(self.unanalyzed_files))
        
        percent_format = workbook.add_format({'num_format': '0.00"%"'}) 
        
        worksheet.write(2, 0, 'Percentage of unanalyzed files')
        
        analyzed_count = len(self.analyzed_files)
        unanalyzed_count = len(self.unanalyzed_files)
        total = analyzed_count + unanalyzed_count
        percentage = 0
        
        if total:
            percentage = unanalyzed_count / total * 100
            worksheet.write(2, 1, math.ceil(percentage), percent_format)
        
        # unhandled detected languages and their remediation
        
        format = workbook.add_format({'bold': True, 'font_color': 'green'})
        
        worksheet.write(4, 0, 'Detected languages with unanalyzed files', format)
        worksheet.write(4, 1, 'Number of files', format)
        worksheet.write(4, 2, 'Recommendation', format)
        worksheet.write(4, 3, 'Documentation', format)
        row = 5
        
        for language in self.languages_with_unanalysed_files:
            worksheet.write(row, 0, language.name)
            worksheet.write(row, 1, len(self.unanalysed_files_per_languages[language]))
            
            core = language.has_core()
            extension = language.has_ua()
            
            if core:
                worksheet.write(row, 2, 'Use %s analyzer' % core)
            elif extension:
                worksheet.write(row, 2, 'Use extension %s' % extension[0])
                worksheet.write(row, 3, '%s' % extension[1])
                
            row += 1
            
        return percentage
    
    def list_files(self, workbook):
        """
        For debug. 
        Fill in a worksheet with list of files + types
        """
        worksheet = workbook.add_worksheet('Analyzed Files List')
        
        worksheet.write(0, 0, 'Type')
        worksheet.write(0, 1, 'Path')
        
        row = 1
        
        for f in self.application.get_files():
            if hasattr(f,'get_path') and f.get_path():
                if not ".net generated files" in f.get_path():
    
                    worksheet.write(row, 0, f.get_type())
                    worksheet.write(row, 1, f.get_path())
                    
                    row += 1
    
        # add filters from (0, 0) to (1, row)
        worksheet.autofilter(0, 0, row, 0)        
    
    def list_unanalysed(self, workbook):
    
        # unanalysed files
        worksheet = workbook.add_worksheet('Files Not Analyzed')
        
        files = self.unanalyzed_files
    
        # order the data according to something stable : language name + path 
        files_per_language = self.unanalysed_files_per_languages
    
        # fill in report
        worksheet.write(0, 0, 'Language')
        worksheet.write(0, 1, 'Path')
        row = 1
        width = 30 
        
        for language in files_per_language:
            
            for _file in files_per_language[language]:
                worksheet.write(row, 0, str(language))
                worksheet.write(row, 1, str(_file.path))
                row += 1
                
                width = max(width, len(str(_file.path)))
        
        # auto set width of column (max width have been calculated along the way)
        worksheet.set_column(1, 1, width)
        
        # add filters from (0, 0) to (1, row)
        worksheet.autofilter(0, 0, row, 0)        
    
    def get_language(self, name):
        """
        Get a language per name.
        """
        if name in self.languages:
            return self.languages[name]
        
        result = Language(name)
        self.languages[name] = result 
        return result
    
    def __get_unanalysed_files(self):
        """
        Find all unanalyzed file of an application
        
        :rtype: collection of File
        
        Those files are not present in KB's application
        They are text files or xml files
        Some files are excluded by known extensions
        """
        all_files = set()
        # get root path
        for root in self.root_path:
        
            logging.info("Using Source root path : %s", root)
            
            # paranoid : if root path is too short (C: for example) skip
            if root == PureWindowsPath('C:\\') or root == PureWindowsPath('C:'):
                logging.info("Source root path found is invalid, aborting.")
                continue
        
            logging.info("Scanning Source root path content...")
            all_files |= self.__scan_all_files(str(root))

    
        analysed_files = self.analyzed_files
    
        logging.info("Comparing files...")
        
        unanalysed_files = all_files - analysed_files
        
        # first exclude some useless, already known files
        unanalysed_files = self.__filter_known(unanalysed_files) 
        
        logging.info("Recognizing text files using magic. May take some time...")
        
        unanalysed_files = self.__filter_text(unanalysed_files)
        
        logging.info("Found  %s unanalyzed text files", len(unanalysed_files))
        
        return unanalysed_files
        
    def __get_root_path(self):
        """
        Access the root source pathes of an application if found.
        
        :return: list of PureWindowsPath
        
        It is an approximation of the reality. 
        
        We take all files of the application and take the most common path of those.
        
        Example : 
          
          - S:\SOURCES\D1\f1.txt
          - S:\SOURCES\D2\f1.txt
          
          --> S:\SOURCES
          
        It will miss folders for how no file is analysed : 
        
        root 
          D1 ... some analysed files   
          D2.. no analysed files
          
        --> root/D1 and missed D2.
          
        """
        logging.info("Searching for source root path...")
        
        try:
            app = self.application.get_application_configuration()
            
            result = []
            for package in app.get_packages():
                result.append(PureWindowsPath(package.get_path()))

            logging.info("Using packages from CMS")
            
            return result
        
        except:
            logging.info("Using KB heuristic")
        
        pathes = []
        
        for f in self.application.get_files():
            if hasattr(f,'get_path') and f.get_path():
                
                path = f.get_path()
                
                # exclude some known generated files
                if ".net generated files" in path:
                    continue
                
                if path.startswith('['):
                    # inside a jar 
                    continue
                
                pathes.append(path.lower())
    
        common = CommonPath(pathes)
        
        # try common first
        result = common.common()
        if not result or result.endswith(':'):
            # if pathological then natural
            result = common.natural()

        result = result.lower()

        # convention : normally application root is ...\deploy\<application name>
        guess = '\\deploy\\' + self.application.name.lower()
        if guess in result:
            logging.info('Found deploy\<app name>. Thank you, following convention renders my job easier.')
            result = result[0:result.find(guess)]+guess

        return [PureWindowsPath(result)]
    
    
    def __get_analysed_file_pathes(self):
    
        files = [f for f in self.application.get_files() if hasattr(f, 'get_path')]
        return set([File(f.get_path()) for f in files if f.get_path()])
        
    
    def __scan_all_files(self, root):
        """
        Give all file of a folder
        
        """
        
        # give a limit of number of scanned files to avoid pathological cases 
        limit = 200000
        
        result = set()
        
        
        for dirname, _, filenames in os.walk(root):
        
            # print path to all filenames.
            for filename in filenames:
                result.add(File(os.path.join(dirname, filename)))
                
                # paranoid
                if len(result) > limit:
                    return result
                
                
        return result
    
    
    def __filter_known(self, files):
        """
        Filter out files considered as not interesting.
        
        jars, dlls, txt files etc...
        VAST....uax, VAST...src
        """
        
        # skipping by glob style file patterns
        # @see https://docs.python.org/3.4/library/glob.html
        excluded_patterns = [
                             # cast extractions
                             "VAST*.src", 
                             "*.uax",
                             "*.uaxdirectory",
                             
                             # assembly extraction
                             "PE.CastPeDescriptor",
                             
                             # binaries
                             "*.jar",
                             "*.dll",
                             "*.exe",
                             "*.pdf",
                             
                             # ms build
                             "*/Debug/*",
                             "*/Release/*",
                             
                             # svn
                             "*.mine",
                             "*.theirs", 
                             
                             # Git 
                             ".gitignore", 
                             "*.gitattributes",
                             
                             # Apache
                             "*.htaccess",
                             
                             # csshint
                             ".csslintrc",
                             
                             # Bower 
                             ".bowerrc", 
                             
                             # Checkstyle 
                             "checkstyle.xml", 
                             
                             # Travis 
                             "travis.yml", 
                             
                             # sonar 
                             "sonar.yml",    
                             
                             # Gatling Performance Testing 
                             "gatling.conf",    
                             
                             # Docker 
                             "Dockerfile",                                
                             
                             # npm
                             ".npmignore", 
                             
                             # jshint
                             ".jshintrc",
                             ".jshintignore", 
                             
                             # JSCS : Javascript code style linter and formatter 
                             ".jscsrc", 
                             ".eslintignore", 
                             
                             # Maven wrappers 
                             "mvnw", 
                             
                             # EditorConfig 
                             ".editorconfig", 
                             
                             # eclipse, do we need to exclude ?
                             "pom.xml", 
                             ".project",
                             ".classpath",
                             
                             # Various
                             "*.log",
                             "*.txt",
                             "*.md", # markdown
                             "COPYING", 
                             "LICENSE",
                             "*.csv",
                             "*.xsd", # schema definition... not interesting 
                             
                             # .h are not interesting, for example external .h and interesting is .cpp
                             "*.h",
                             
                             # skipped by analyser
                             "package-info.java",
                             
                             # java deployment
                             "MANIFEST.MF",
                             
                             # microsoft database project
                             "*.dbp",
                             # microsoft project...
                             "*.sln",
                             "*.vspscc",
                             "*.vdproj",
                             "*.csproj",
                             "*.vssscc",
                             "*.csproj.user",
                             
                             # xcode 
                             "*.xcbkptlist", # breakpoints
                             "*.xcwordspacedata",
                             
                             # do not laugh, I have seen it 
                             "tnsnames.ora",
                             
                             # abap useless extracted files
                             '*CT.abap',
                             '*CP.abap',
                             'SAP*.sap.xml',
                             'SAP*.SQLTABLESIZE',
                             ]
        
        # this time full regular expressions
        complex_patterns = [
                            # svn example : .r2681
                            ".*\.r[0-9]+",
                            ".*\\\.svn\\.*",
                            # eclipse config
                            ".*org\.eclipse\..*", 
                            # abap program description
                            ".*\\PG_DESCR_.*\.xml"
                            ]
        
        
        def is_excluded(f):
            
            for pattern in excluded_patterns:
                if f.match(pattern):
                    return True
    
            for pattern in complex_patterns:
                
                if re.match(pattern, str(f)):
                    return True
    
            return False
        
    
        for f in files:
    
            # skip some
            if is_excluded(f.path):
                continue
            
            yield f
        
    
    def __filter_text(self, files):
        """
        return text files only
        """
        result = []
        
        m = {}
        
        for f in files:
            m[f.path] = f
        
        
        # consider only those that are text only
        magic = run_magic(m.keys())
    
        for f in magic:
            
            mime = f[1]
            content_type = mime[0]
            
            # @todo : may have other combinations to handle 
            if content_type == 'text' or len(mime) > 1 and mime[1] == 'xml':
                
                _file = m[PureWindowsPath(f[0])]
                # stores mime info on the file object
                _file.mime_type = mime
                result.append(_file)
    
        return result

    def __get_languages(self):
        
        logging.info('Scanning languages...')
        files = self.unanalyzed_files
    
        for _file in files:
            
            language = _file.get_language(self)
            self.languages_with_unanalysed_files.add(language)
            if not language in self.unanalysed_files_per_languages:
                # sorted also here
                self.unanalysed_files_per_languages[language] = SortedSet()
            
            self.unanalysed_files_per_languages[language].add(_file)


class File:
    """
    Represent a file and informations found on it
    """
    
    def __init__(self, path):
        self.path = PureWindowsPath(path)
        self.mime_type = None
        # languages recognized by extensions
        self.languages = recognise_language(path)
        self.language = "unknown"
    
    def set_mime(self, mime):
        """
        Set mime type recognized by libmagic
        
        :param: mime a pair of string
        
        @see  http://www.iana.org/assignments/media-types/media-types.xhtml   
        """
        self.mime_type = mime

    def get_language(self, application):
        """
        Get the recognized language of the file. 
        """
        
        if self.languages:
            # if several choices... ????
            self.language = self.languages[0][0]
        else:
            
            # try mime type :
            if self.mime_type == ['application', 'xml']:
                self.language = 'XML'
            elif self.mime_type == ['text', 'html']:
                self.language = 'HTML'
        
        return application.get_language(self.language)
        
    def __eq__(self, other):
        return self.path == other.path    

    def __lt__(self, other):
        return self.path < other.path
        
    def __hash__(self):
        return hash(self.path)


class Language:
    
    def __init__(self, name):
        self.name = name

    def has_core(self):
        """
        Return the associated core analyzer when available
        """
        map = {'C#':'.Net',
               'C++':'C/C++',
               'C':'C/C++',
               'Java':'JEE', 
               'Java Server Pages':'JEE',
               'COBOL':'Mainframe',
               'Pascal':'PowerBuilder',
               'ABAP':'SAP',
               'Visual Basic':'VisualBasic',
               }
        
        try:
            return map[self.name]
        except:
            pass
        

    def has_ua(self):
        """
        returns the extension/ua when available
        
        a couple : extension id + link to documentation
        """
        # @todo : list them all... 
        map = {
               'PHP':('com.castsoftware.php', 'http://doc.castsoftware.com/display/DOCEXT/PHP+1.1'),
               'FORTRAN':('com.castsoftware.fortran', 'http://doc.castsoftware.com/display/DOCEXT/Fortran+1.0'),
               'Shell':('com.castsoftware.shell', 'http://doc.castsoftware.com/display/DOCEXT/SHELL+1.0'),
               'ActionScript':('com.castsoftware.flex', 'http://doc.castsoftware.com/display/DOCEXT/Flex+1.0'),
               'SQL':('com.castsoftware.sqlanalyzer', 'http://doc.castsoftware.com/display/DOCEXT/SQL+Analyzer+-+1.0'),
               'Python':('com.castsoftware.python', 'TBD'),
               'EGL':('com.castsoftware.egl', 'http://doc.castsoftware.com/display/DOCEXT/EGL+1.0'),
               'PL1':('com.castsoftware.pl1', 'http://doc.castsoftware.com/display/DOCEXT/PL1+1.0'),
               'Perl':('com.castsoftware.perl', 'https://confluence.castsoftware.com/display/WwSEs/Perl+Extension+Description'),
               'RPG':('com.castsoftware.rpg', 'http://doc.castsoftware.com/display/DOCEXT/RPG+2.0'),
               }

        try:
            return map[self.name]
        except:
            pass

    def __eq__(self, other):
        return self.name == other.name    

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.name



    
    