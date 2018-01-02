import os
from linguist.languages import languages


def recognise_language(filepath):
    """
    Return a list of languages recognized by extensions.
    
    Inspired from https://github.com/liluo/linguist
    
    @todo : also recognise XML frameworks in several technologies
    """
    ext = os.path.splitext(filepath)[1]
    fileextractname = os.path.split(filepath)[1]

    result = []
    
    for language, data in languages.items():
        
        if data["primary_extension"] == ext or ('extensions' in data and ext in data['extensions']):
            result.append((language, data))
            
            
        if ('filenames' in data and fileextractname in data['filenames']):
            result.append((language, data))

    return result
