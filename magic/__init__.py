import subprocess
import tempfile
import os
import logging
import traceback


def run_magic(files):
    """
    Run libmagic on a collection of file path and return a list of 
    
      (file_path, ('category', 'sub category'), encoding)
    
    @see http://www.iana.org/assignments/media-types/media-types.xhtml for a complete list of media types
    
    For example : 
    
    ('S:\\SOURCES\\RTE\\tasklet\\HistorizeHousingTasklet.java', ['text', 'x-java'], 'utf-8')
    
    dir_path is the path containg 
    
    """
    bin_path = os.path.join((os.path.dirname(__file__)), 'bin')
    
    files_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False)
    for f in files:
        try:
            files_file.write(str(f) + '\n')
        except:
            # file name can be encoded with chineese ?
            pass
    files_file.close()    
    
    command = '"' + bin_path +'/file.exe" --mime --no-pad -m "' + bin_path + '/magic.bin" -f "' + files_file.name + '"'

    result = []
    
    try:
        
        p = subprocess.Popen(command,universal_newlines=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr = subprocess.PIPE)
        (out,_) = p.communicate()
        magics = out.splitlines()
        
        os.remove(files_file.name)
        
        for line in magics:
            
            elements = line.split('; ')
            
            # @todo : elements[1].split('/') do not always return a pair...
            mime = ('unknown', '')
            try:
                mime = elements[1].split('/')
                if len(mime) < 2:
                    mime = (mime[0], '')
            except:
                # no mime for some files
                pass
            
            charset = None
            try:
                charset = elements[2].split('=')[1]
            except:
                # no charset for some files
                pass
            
            result.append((elements[0], mime, charset))
            
        
    except:

        # something bad happened 
        # keep all 
        logging.info('an issue occurred during magic, skipping filtering.\n' + traceback.format_exc())
        for f in files:
            
            result.append((str(f), ['text'], 'utf-8'))
    
    return result


