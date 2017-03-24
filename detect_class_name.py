import xml.etree.ElementTree as eTree
import re


def get_words_with_point(text):
    """
    :param text: string without ' ', \n, \t and \r
    """
    list_dot_word = re.split("[, =\-\n\r\t!?():]+", text)
    set_list = set()
    if len(list_dot_word) >= 2:
        return set_list
    for dot_word in list_dot_word:
        if dot_word and '.' in dot_word:
            dot_word = dot_word.strip('.')
            if '.' in dot_word:
                set_list.add(dot_word)
    """
    if len(list) >= 2:
    return set()
    """
    return set_list

def parse_children(root):
    """
    :param root: root tags of .xml file
    """
    attrib_list = set()
    for child in root:
        text = child.text
        if text:
            text = text.strip(' \n\t\r')
            attrib_list = attrib_list | get_words_with_point(text)
        attrib_list = attrib_list | parse_children(child)
        for attribute_name, attribute_value in child.attrib.items():
            if '.' in attribute_value:
                attrib_list.add(attribute_value)
    """
    returns list of attribute_value 
    """
    return attrib_list

def parse_file(file_name):
    """
    :param file_name: file to parse, str or object having path attribute convertible to str
    """
    
    if hasattr(file_name, 'path'):
        file_name = str(file_name.path)
    
    try:
        tree = eTree.parse(file_name)
        root = tree.getroot()
        l = parse_children(root) 
        l = sorted(l)
        return (l)
    except eTree.ParseError:
        # there exist in nature some files that are not 'pure' xml
        return []
    """
    returns list of children in file
    """
    
def parse_string(s):
    root = eTree.fromstring(s)
    l = parse_children(root) 
    l = sorted(l)
    return (l)

def search_classes(file_paths, classes):
    """
    :param file_paths: list of string, files paths  
    :param classes: list of Object
    """
    dict_classes = {}
    list_names = {}
    names_in_file = []

    for file_name in file_paths:
        names_in_file = parse_file(file_name)
        list_names[file_name] = names_in_file
        
    for object_name in classes:
        object_name = object_name.get_qualified_name()
        
        for file_name, names_in_file in list_names.items():
            if object_name in names_in_file:
                # file_name contains object_name
                if not file_name in dict_classes:
                    dict_classes[file_name] = []
                
                dict_classes[file_name].append(object_name)
    """
    returns dictionary of {file_path : [list_of_objects] }
    """
    return dict_classes

#parse_file('F:/python_work/LeadDesignPsi.hbm.xml')
