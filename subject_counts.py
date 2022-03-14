from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def count_categories():
    csvpath = Path.cwd()/"res/goodreads_library_export+subjects.csv"
    df = pd.read_csv(csvpath)
    pd.set_option('display.max_rows', None)
    df_count = df.Subjects.str.get_dummies(sep="~").sum().sort_values(ascending=False)
    # drop some nonsense categories
    nonsense_categories = ['accessible book', 'protected daisy', '=', 'general', '"', 'ficción']
    df_count = df_count.drop(nonsense_categories)
    #show only top X categories
    top_x = df_count.head(20)
    print(top_x)
    top_x.plot(kind='pie')
    plt.show()


count_categories()
