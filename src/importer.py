'''
Created on 16 May 2014

@author: Bleier
'''
import xlrd, os, sys, getopt
from optparse import OptionParser
import datetime
import shutil
from helper import item_to_pickle, get_text_files
from txt_classes import TxtItem, TxtCorpus, TxtItemLetterExcel, TxtItemTextFile
from settings import TIMESTAMP_COL, TRANSCRIPTION_COL, TXT_ID, PAGE_COL

def make_txt_corpus(corpus_dir_path, txt_items=None, path_to_txt_items=None, corpus_file_name=None, corpus_dict_name=None, corpus_vect_name=None):
    
    if not corpus_file_name:
        corpus_file_name = "text_corpus.pickle"
    if txt_items:
        path_to_txt_items = corpus_dir_path + os.sep + "txtitems.pickle"
        item_to_pickle(path_to_txt_items, txt_items) 
    
    corpus = TxtCorpus(path_to_txt_items)
    #make a dictionary of the words in the corpus
    if not corpus_dict_name:
        corpus_dict_name = corpus_dir_path + os.sep + "text_corpus.dict"
    if not corpus_vect_name:
        corpus_vect_name = corpus_dir_path + os.sep + "text_vect_corpus.pickle"
    corpus.add_vector_corpus_and_dictionary(corpus_vect_name, corpus_dict_name)
    item_to_pickle(corpus_dir_path + os.sep + corpus_file_name, corpus)
    return corpus

def txt_to_object(file_name, txt_id, page, nr):
    f = open(file_name, "r")
    txt = f.read()
    f.close()
    t = TxtItem()
    t.add_attr("file", file_name)
    t.add_attr("Letter", file_name)
    t.add_page(page, nr, txt) # add also pagenumber and timestamp before the string!
    t.unique_name = txt_id
    return t

def get_texts_from_files(dir_path, corpus_dir, file_ext=".txt"):
    """
    Given a directory path and a file path the function gets first a list of text files form the location 'dir_path'
    The text of each text file will be stored in a TxtItem instance, and the instance will be stored in a list
    The list will be pickled to 'corpus_file_path' and TxtCorpus created that uses this pickle file as source data
    The TxtCorpus will be returned
    """
    documents = get_text_files(dir_path, file_ext)
    text_location_dict = {}
    texts = []
    for idx, file_name in enumerate(documents):
        unique_name = file_name.split(".")[0]
        file_path_to_text_file = dir_path + os.sep + file_name
        t = TxtItemTextFile(file_path_to_text_file, unique_name)
        new_file_path = corpus_dir + os.sep + "txt" + os.sep + file_name
        t.add_new_filepath(new_file_path)
        
        texts.append(t)
        try:
            #dictionary to map text ids with object location - for quick access of individual items
            text_location_dict[unique_name] = len(texts)-1
        except KeyError: ("Error: The unique name for the object is already used. The imported text files seem to have the same name.")
    return texts, text_location_dict

def get_texts_from_Excel(file_name_excel, corpus_dir):
    """
    The function gets data from an Excel file and turn it into a TxtCorpus
    The parameter file_name_excel is a valid file path to an excel file containing texts and metadata
    The function returns a TxtCorpus
    """
    #Creates an object of type Book from xlrd.book object
    try:
        wb = xlrd.open_workbook(filename=file_name_excel, encoding_override="utf-8")
    except xlrd.XLRDError:
        print "The file at the location {} is not a valid excel format".format(file_name_excel)
        sys.exit()
    sheet = wb.sheet_by_index(0)
    texts = []
    text_location_dict = {}
    try:
        for row in range(1,sheet.nrows):
            row_dict = {}
            for col in range(sheet.ncols):
                if sheet.cell(row,col).ctype == 3: # 1 is type text, 3 xldate
                    date_tuple = xlrd.xldate_as_tuple(sheet.cell_value(row,col), wb.datemode)
                    date_py = datetime.datetime(*date_tuple)
                    row_dict.update({sheet.cell_value(0,col): date_py}) # a datetime.datetime obj is stored
                else:
                    row_dict.update({sheet.cell_value(0,col):sheet.cell_value(row,col)})
            unique_name = str(row_dict[TXT_ID])
            t = TxtItemLetterExcel(unique_name, **row_dict)
            
            if t.unique_name not in text_location_dict:
                t.add_page(getattr(t, PAGE_COL), getattr(t, TIMESTAMP_COL), getattr(t, TRANSCRIPTION_COL)) #note: has to be tested if attributes are correctly imported!
                texts.append(t)
                #dictionary to map text ids with object location - for quick access of individual items
                text_location_dict[t.unique_name] = len(texts)-1
            else:
                # l.Translation - 'Translation' is the name that was given to the column in the Excel file - if the name changes the attribute will change too
                texts[text_location_dict[t.unique_name]].add_page(getattr(t, PAGE_COL), getattr(t, TIMESTAMP_COL), getattr(t, TRANSCRIPTION_COL))
    except KeyError:
        print "KeyError: possible cause - column names in settings file are not found in the excel source file"
        sys.exit()
    #add a txt file folder to each object
    file_path = corpus_dir + os.sep + "txt"
    for txt_item in texts:
        file_name = txt_item.unique_name + ".txt"
        txt_item.add_txt_file(file_path, file_name)
    return texts, text_location_dict


def main(mode, file_name_excel=None, corpus_dir=None, txt_dir_path=None):
    if not corpus_dir:
        current_dir = os.getcwd()
        corpus_dir = current_dir + os.sep + "corpus"
        print "No corpus directory was passed as argument. The corpus was created in {0}".format(corpus_dir)
    if os.path.isdir(corpus_dir):
        inp = raw_input("The directory already exists, shall it be overwritten?Y/N: ")
        if inp == "Y" or inp == "y":
            shutil.rmtree(corpus_dir)
            
        elif inp == "N" or inp == "n":
            return None
        else:
            print "Wrong input!"
            return None
    os.mkdir(corpus_dir)
    if mode == "excel":
        txtItems, id2texts = get_texts_from_Excel(file_name_excel, corpus_dir)
        item_to_pickle(corpus_dir + os.path.sep + "corpusfiles.pickle", txtItems)
    elif mode == "txt":
        txtItems, id2texts = get_texts_from_files(txt_dir_path, corpus_dir, file_ext=".txt")
        item_to_pickle(corpus_dir + os.sep + "corpusfiles.pickle", txtItems)
            

if __name__ == "__main__":
    key_args = {}
    parser = OptionParser()
    parser.add_option('-m', '--mode', dest="mode", action="store", 
                            help="requires -fx or -ft option. Mode settings: txt/excel")
    parser.add_option('-f', '--file_name_excel', dest="file_name_excel", 
                            action="store", help="file_name_excel: path to an excel file, used if -m set to 'excel")    
    parser.add_option('-d', '--txt_dir_path', dest="txt_dir_path", action="store", 
                            help="txt_dir_path: path to an folder with txt file, used if -m set to 'txt")    
    parser.add_option('-c', '--corpus_dir', dest="corpus_dir", action="store", 
                            help="corpus_dir: optional path to a directory where the imported corpus should he stored")    
    
    (options, args) = parser.parse_args()

    #validation
    if options.mode == "txt":
        if options.txt_dir_path:
            if os.path.isdir(options.txt_dir_path):
                key_args["mode"] = options.mode
                key_args["txt_dir_path"] = options.txt_dir_path
            else:
                parser.error("The path supplied is not a valid directory")
        else:
            parser.error("No path to text files supplied")
    elif options.mode == "excel":
        if options.file_name_excel:
            if os.path.isfile(options.file_name_excel):
                key_args["mode"] = options.mode
                key_args["file_name_excel"] = options.file_name_excel
            else:
                parser.error("The path supplied is not a valid file path")
        else:
            parser.error("No path to excel file found")
    else:
        parser.error("A mode -m option has to be set (txt/excel)")
    if options.corpus_dir:
            key_args["corpus_dir"] = options.corpus_dir
    main(**key_args)
    print "corpus successfully created"
