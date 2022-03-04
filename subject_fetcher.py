#!/usr/bin/env python

''' Script to find and add book subject data to an exported goodreads library.
    Uses the open library api.
    Shamefully copied from my isbn_updater script.
    Use as refactoring challenge later'''

from pathlib import Path
import csv
import pandas as pd
import requests
import json

# Because if I couldn't find ISBN data on openlibrary, won't find subject data either
def not_missing_isbn():
    # import the CSV directly with pandas:
    csvpath = Path.cwd()/"res/goodreads_export.csv"
    dataframe = pd.read_csv(csvpath)
    have_isbn = dataframe.loc[dataframe['ISBN'] != '=""']
    titles = have_isbn['Title'].values
    authors = have_isbn['Author'].values
    isbns = have_isbn['ISBN'].values
    # for title, isbn in zip(titles,isbns):
    #     print(title,"=>",isbn)
    return have_isbn

# query is in this format: https://openlibrary.org/search.json?author=Harper+Lee&title=To+Kill+a+Mockingbird&limit=1&offset=0
# did not do https://openlibrary.org/api/books?bibkeys=ISBN:0062936018&jscmd=data&format=json because too slow for some reason?
def build_query():
    have_isbn = not_missing_isbn()
    base_url = 'http://openlibrary.org/search.json?'
    author_bit = 'author='
    title_bit = '&title='
    query_limit = '&limit=1&offset=0'
    titles = have_isbn['Title'].values
    authors = have_isbn['Author'].values
    # logic for list comprehensions below in isbn_updater.py
    non_bracket_titles = [ title[:title.find('(')].strip() if title.find('(') != -1 else title for title in titles]
    titles_formatted = [title.lower().replace(' ', '+') for title in non_bracket_titles]
    authors_formatted = [author.lower().replace(' ', '+') for author in authors]
    query_urls = [base_url + author_bit + author_formatted + title_bit + title_formatted + query_limit for author_formatted, title_formatted in zip(authors_formatted, titles_formatted)]
    for query in query_urls:
        print(query)

    return query_urls

def fetch_subjects():
    query_urls = build_query()
    have_isbn = not_missing_isbn()
    titles = have_isbn['Title'].values
    isbns = have_isbn['ISBN'].values
    fetched_subjects = dict()
    for isbn, query in zip(isbns, query_urls):
        # print(query)
        try:
            response = requests.get(query)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as err:
            # e.g. DNS failure, refused connection, etc
            print(f"Something went wrong with the connection. Did not find: {isbn}")
            fetched_subjects[isbn] = '=""'
            print(err)
            continue
            # raise SystemExit(err)
        except requests.exceptions.HTTPError as err:
            # eg, url, server and other errors
            print(f"HTTPError. Could not find: {isbn}")
            fetched_subjects[isbn] = '=""'
            print(err)
            continue
            # raise SystemExit(err)

        json_response = response.json()
        if json_response['numFound'] != 0: # we have at least one result
            try:
                subject = json_response['docs'][0]['subject']
                fetched_subjects[isbn] = subject
                print(f"{json_response['docs'][0]['title']} SUBJECTS: {subject}")
            except:
                print(f"No subject info for: {json_response['docs'][0]['title']}")
        else:
            print("NOT FOUND: ",isbn)
            fetched_subjects[isbn] = '=""'

    print(fetched_subjects)

    return fetched_subjects

def update_subjects():
    csvpath = Path.cwd()/"res/goodreads_export.csv"
    master_df = pd.read_csv(csvpath)
    # create new column (subjects)
    master_df["Subjects"] = ""
    fetched_subjects = fetch_subjects()

    for isbn, subject in fetched_subjects.items():
        # "Subjects" cell becomes subject where ISBN cell == isbn
        # subject is a list of multiple subjects: lowercase all then turn to a string split by commas
        subject = [item.lower() for item in subject]
        master_df.loc[master_df.ISBN == isbn, "Subjects"] = ','.join(subject)
        # finally, export dataframe to file
        output_file = Path.cwd()/"res/goodreads_export_subjects.csv"
        master_df.to_csv(output_file, encoding='utf-8', index=False)




update_subjects()
