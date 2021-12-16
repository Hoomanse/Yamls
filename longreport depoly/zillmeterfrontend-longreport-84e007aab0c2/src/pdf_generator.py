import os
from os.path import exists


def word_to_pdf(file):
    os.system(f'doc2pdf \"{file}.docx\"')
    while not exists(f'{file}.pdf'):
        pass
    os.remove(f'{file}.docx')
