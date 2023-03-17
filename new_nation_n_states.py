import pandas as pd


def load_regions(filename):
    states_df = (pd.read_csv(filename, usecols=[1, 3], names=['abbrev', 'pop'])
                   .sort_values(by='pop', ascending=False)
                )
    return states_df


def load_borders(filename):
    df = pd.read_csv(filename, usecols=[1], names=['target'], header=0)
    df[['target', 'neighbor']] = df['target'].str.split('-', 1, expand=True)
    borders_df = pd.DataFrame({'target': df['target'].append(df['neighbor'])})
    borders_df['neighbor'] = df['neighbor'].append(df['target'])
    borders_df = borders_df.reset_index(drop=True)

    return borders_df


def combine_borders_states(states_df, borders_df):
    stateb_porders = borders_df.merge(
        states_df, left_on='neighbor', right_on='abbrev', how='left').drop(columns=['abbrev'])

    return stateb_porders


def new_nation_n_states(n=1, region_filename='usstates.csv', border_filename='border_data.csv'):
    states = load_regions(region_filename)
    borders = load_borders(border_filename)
    b_p = combine_borders_states(states, borders)

    # Store some usful values
    largest_pop = states.iloc[0, 1]
    smallest_pop = states.iloc[-1, 1]

    # Pick top population states as starting points
    start_state = states.head(8)

    # TODO: It is possible to use map to replace the loop?
    for i in range(n-1):
        df_list = []
        # Merge depending on how many columns in start_state dataframe
        for j in range(start_state.shape[1] - 1):
            # print(i, j)
            # TODO: Anyway to improve merge performance? set_index and join?
            df = start_state.merge(
                b_p, left_on=start_state.columns[j], right_on='target', suffixes=('_l', '_r'))
            df_list.append(df)

        # Concatenate the dataframes
        start_state = pd.concat(df_list, ignore_index=True)

        # Drop those try to merge back to exists states
        start_state = start_state[~start_state.drop(columns="neighbor").isin(start_state["neighbor"]).any(1)]

        # Adjust the dataframe into the next iteration format
        start_state['pop'] = start_state['pop_l'] + start_state['pop_r']

        # TODO: not the right logic to drop: what if sum of pop of different states are same?
        start_state = (start_state.drop_duplicates(subset='pop')
                                  .drop(columns=['target', 'pop_l', 'pop_r'])
                                  .rename(columns={'abbrev': f'ST{i}', 'neighbor': 'abbrev'})
                       )

        # Drop rows that have too big gap compares to the maximum pop (Second Larget - Smallest)
        # The current max combination will increase at least smallest pop in the worst case, 
        # For other candidates, the best case is to find the second largest pop in the best case
        #start_state = start_state[start_state['pop'] > start_state['pop'].max() - (largest_pop - smallest_pop)]
        start_state = start_state.sort_values(by='pop', ascending=False).head(100)


    new_nation = start_state[start_state['pop'] == start_state['pop'].max()]

    return tuple(new_nation.iloc[0, :-1]), new_nation.iloc[0, -1]
