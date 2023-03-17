import pandas as pd


def load_regions(filename):
    states_df = (pd.read_csv(filename, usecols=[1, 3], names=['abbrev', 'pop'])
                   .sort_values(by='pop', ascending=False))
    
    return states_df


def load_borders(filename):
    df = pd.read_csv(filename, usecols=[1], names=['target'], header=0)
    df[['target', 'neighbor']] = df['target'].str.split('-', 1, expand=True)
    borders_df = pd.DataFrame({'target': df['target'].append(df['neighbor'])})
    borders_df['neighbor'] = df['neighbor'].append(df['target'])
    borders_df = borders_df.reset_index(drop=True)

    return borders_df


def combine_state_borders(states_df, borders_df):
    df = borders_df.merge(states_df, left_on='neighbor', right_on='abbrev', how='inner').drop(columns=['abbrev'])

    return df


def new_nation_with_pop(p=40, region_filename='usstates.csv', border_filename='border_data.csv'):
    states = load_regions(region_filename)
    borders = load_borders(border_filename)
    s_b = combine_state_borders(states, borders)

    # Pick top five population states as starting points
    start_state = states.head(8)

    # Store some usful values
    largest_pop = states.iloc[0, 1]
    smallest_pop = states.iloc[-1, 1]
    max_pop = start_state[start_state['pop'] == start_state['pop'].max()].iloc[0, -1]
    i = 0

    while max_pop < p * 10 ** 6:
        df_list = []
        for j in range(start_state.shape[1] - 1):
            # print(i, j)
            df = start_state.merge(s_b, left_on=start_state.columns[j], right_on='target', suffixes=('_left', '_right'))
            df_list.append(df)

        # Concatenate the dataframes
        start_state = pd.concat(df_list, ignore_index=True)

        # Drop those try to merge back to exists states
        start_state = start_state[~start_state.drop(columns="neighbor").isin(start_state["neighbor"]).any(1)]

        # Adjust the dataframe into the next iteration format
        start_state['pop'] = start_state['pop_left'] + start_state['pop_right']

        start_state = (start_state.drop(columns=['target', 'pop_left', 'pop_right'])
                                  .drop_duplicates(subset='pop')
                                  .rename(columns={'abbrev': f'ST{i}', 'neighbor': 'abbrev'})
                        )

        # Drop rows that have too big gap compares to the maximum pop (Larget - Smallest)
        # start_state = start_state[start_state['pop'] > start_state['pop'].max() - (largest_pop - smallest_pop)]
        start_state = start_state.sort_values(by='pop', ascending=False).head(500)

        max_pop = start_state[start_state['pop'] == start_state['pop'].max()].iloc[0, -1]
        i += 1

    new_nations = start_state[start_state['pop'] >= p * 10 ** 6]
    new_nations_list = [tuple(new_nations.iloc[i, :-1]) for i in range(new_nations.shape[0])]

    return new_nations_list
