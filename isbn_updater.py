#!/usr/bin/env python

''' Script to check for and fill in missing book ISBNs from an exported goodreads library.
    Uses the open library api. '''
# to do:
# allow user option to just give their goodreads username/profile, export their books
# create gui to allow user to select exported CSV file

from pathlib import Path
import csv
import pandas as pd
import requests
import json

# Broken down to multiple functions.
# First finds and optionally displays the titles missing ISBN
# Second builds correct json query
# Third fetches missing ISBN data and returns a dictionary {Title:ISBN}
# Fourth updates CSV with missing ISBN values

def find_missing_isbn():
    # import the CSV directly with pandas:
    csvpath = Path.cwd()/"res/goodreads_library_export.csv"
    dataframe = pd.read_csv(csvpath)
    # title_count = len(dataframe)
    # missing_isbn_count = dataframe.loc[:,'ISBN'].eq('=""').sum()
    # print(f"{missing_isbn_count} out of {title_count} Books have missing ISBNs")

    # optional: Display missing ISBNs:
    # print("\nThe books missing ISBNs are:\n")
    missing = dataframe.loc[dataframe['ISBN'] == '=""']
    titles = missing['Title'].values
    authors = missing['Author'].values
    for title, author in zip(titles,authors):
        # print(title,"=>",author)
        pass
    return missing


def build_query():
    # query is in this format: http://openlibrary.org/search.json?q=one+hundred+years+of+solitude&limit=1&offset=0
    # to do: https://openlibrary.org/search.json?author=Harper+Lee&title=To+Kill+a+Mockingbird&limit=1&offset=0
    missing = find_missing_isbn()
    base_url = 'http://openlibrary.org/search.json?q='
    query_limit = '&limit=1&offset=0'  # limit to 1 query result set
    titles = missing['Title'].values
    authors = missing['Author'].values
    # remove info in brackets if it exists.
    # some titles are in this format: 'Slave to Sensation (Psy-Changeling, #1)'. Change to: 'Slave to Sensation'
    # Explanation for logic used below:
    # title.find('(') returns index where bracket starts, -1 if not found. title[:index] returns title up to start of brackets. strip() trailing spaces
    # List comprehension Logic[NEW_TITLE if CONDITION else TITLE for TITLE in OLDLIST]
    non_bracket_titles = [ title[:title.find('(')].strip() if title.find('(') != -1 else title for title in titles]
    titles_formatted = [title.lower().replace(' ', '+') for title in non_bracket_titles]
    authors_formatted = [author.lower().replace(' ', '+') for author in authors]
    query_urls = [base_url + title_formatted + query_limit for title_formatted in titles_formatted]

    return query_urls

# Get response for each url in query_urls
def fetch_isbn():
    # To Do: implement rate limiter.
    query_urls = build_query()
    missing = find_missing_isbn()
    # get the list of titles, to create k:v pairs with title(k) : isbn(v)
    missing_titles = missing['Title'].values
    fetched_isbns = dict()
    for title, query in zip(missing_titles,query_urls):
        # print(query)
        try:
            response = requests.get(query)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as err:
            # e.g. DNS failure, refused connection, etc
            print("Something went wrong with the connection")
            print(err)
            continue
            # raise SystemExit(err)
        except requests.exceptions.HTTPError as err:
            # eg, url, server and other errors
            print(err)
            continue
            # raise SystemExit(err)

        json_response = response.json()
        if json_response['numFound'] != 0: # we have at least one result
            isbn = json_response['docs'][0]['isbn'][0]
            fetched_isbns[title] = isbn
            print(f"{json_response['docs'][0]['title']} ISBN: {isbn}")
        else:
            print("NOT FOUND: ",json_response['q'])
            fetched_isbns[title] = '=""'

    return fetched_isbns



# update dataframe that had missing ISBNS:
def update_isbn():
    # first, create backup
    orig_csvpath = Path.cwd()/"res/goodreads_library_export.csv"
    bak_csvpath = Path.cwd()/"res/goodreads_library_export.csv.bak"
    bak_csvpath.write_text(orig_csvpath.read_text())
    orig_df = pd.read_csv(orig_csvpath)
    print("Backup of original CSV done!")
    title_count = len(orig_df)
    missing_isbn_count = orig_df.loc[:,'ISBN'].eq('=""').sum()
    print(f"{missing_isbn_count} out of {title_count} Books have missing ISBNs")
    print("**********************************")
    print("\nFetching missing data...\n")

    # second, update dataframe
    fetched_isbns = fetch_isbn()
    for title, isbn in fetched_isbns.items():
        # "ISBN" cell becomes isbn where Title cell == title
        orig_df.loc[orig_df.Title == title, "ISBN"] = isbn

    # third, export dataframe to file
    output_file = Path.cwd()/"res/goodreads_library_export_updated.csv"
    orig_df.to_csv(output_file, encoding='utf-8', index=False)

    #finally, some update info to user:
    not_found = []
    not_found_count = 0
    for title in fetched_isbns:
        if fetched_isbns[title] ==  '=""':
            not_found_count += 1
            not_found.append(title)

    print("\n*******************************")
    print(f"Tried to update {len(fetched_isbns)} ISBNs ")
    print(f"Did not find {not_found_count} ISBNs")
    print("\nThey are:\n")
    for title in not_found:
        print(title)
    print(f"\nUpdated CSV saved to: {output_file}")
    print("\nGoodbye!")


update_isbn()
