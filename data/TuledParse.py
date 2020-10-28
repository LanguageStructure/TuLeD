import pandas as pd
import csv


def raw_to_dict():
    main_data_df = pd.read_csv("tuled.tsv", sep="\t", header=0, encoding='utf8')
    main_data_df = main_data_df.iloc[:-22]  # the last lines in the file is irrelevant meta-data
    main_data_df = main_data_df.drop(columns=['ID', 'VALUE', 'ALIGNMENT', 'COGNACY'])
    main_data_df.rename({'DOCULECT': 'Language', 'CONCEPT': 'Concept', 'FORM': 'Form',
               'TOKENS': 'Tokens', 'MORPHEMES': 'Morphemes', 'COGID': 'SimpleCognate',
               'COGIDS': 'PartialCognate', 'NOTE': 'Notes', }, axis=1, inplace=True)
    #main_data_df['SimpleCognate'] = main_data_df['SimpleCognate'].apply(int)
    main_data_df.to_csv('preprocessed_data.tsv', sep='\t', index=False, encoding='utf-8')


def tuled_dictionary():
    dict_list = []
    with open('preprocessed_data.tsv', mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter="\t")
        line_count = 0
        for row in csv_reader:
            dict_list.append(row)
            line_count += 1
    return dict_list


def concept_dictionary():
    dict_list = []
    with open('concepts.tsv', mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter="\t")
        for row in csv_reader:
            dict_list.append(row)
    return dict_list


raw_to_dict()
# lists of OrderedDict
tuled = tuled_dictionary()
concepts = concept_dictionary()

for dictionary in tuled:
    for concept_dictionary in concepts:
        for key in concept_dictionary:
            if concept_dictionary['Name'] == dictionary['Concept']:
                dictionary['Portuguese'] = concept_dictionary['Portuguese']
                dictionary['Semantic'] = concept_dictionary['Semantic']
                dictionary['Concepticon'] = concept_dictionary['Concepticon']
                dictionary['Eol'] = concept_dictionary['Eol']

df = pd.DataFrame(tuled)
"""
df = df.drop(columns=['ID', 'VALUE', 'ALIGNMENT', 'COGNACY'])
df.rename({'DOCULECT': 'Language', 'CONCEPT' : 'Concept', 'FORM' : 'Form',
           'TOKENS' : 'Tokens', 'MORPHEMES': 'Morphemes', 'COGID' : 'SimpleCognate',
           'COGIDS' : 'PartialCognate', 'NOTE' : 'Notes',},  axis=1, inplace=True)

df['SimpleCognate'] = df['SimpleCognate'].apply(int)
"""
df.to_csv('main.tsv', sep='\t', index=False, encoding='utf-8')