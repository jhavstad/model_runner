from ggplot import *
import pandas as pd
import logging
import numpy as np

import matplotlib.pyplot as plt

def get_model_sub_strings(column):
    sub1 = column[0: column.index('_')]
    sub2 = column[column.rindex('_')+1:len(column)]
    return (sub1, sub2)

def merge_columns(df):
    col_search = df.columns - ['year']
    col = col_search[0]
    match_cols = list()
    while len(col_search) > 1:
        (sub1, sub2) = get_model_sub_strings(col)
        col_search = col_search - [col]
        for next_col in col_search:
            (sub1_next, sub2_next) = get_model_sub_strings(next_col)
            if sub1 == sub1_next and sub2 == sub2_next:
                match_cols.append([col, next_col, sub1, sub2])
                col_search = col_search - [next_col]
        if len(col_search) > 0:
            col = col_search[0]

    df_new = df['year']
    for match_col in match_cols:
        df_col = df[match_col[0]].fillna(df[match_col[1]])
        df_col.name = match_col[2] + '_' + match_col[3]
        df_new = pd.concat([df_new, df_col], axis=1, join_axes=[df.index])
    return df_new

def get_closest_fit(df, datatype):
    '''
    Find the data frame that is the closest fit to an average of all the data frame columns together
    Input: The data frame with all the mer
    '''
    # Extract the values columns
    columns = df.columns - ['year']
    df_values = df[columns]

    # Create a data frame that contains the average for a row
    # axis=1 to compute the averages along left-right(?) axis, versus the up-down(?) axis
    averages = df_values.mean(axis=1)
    # Fill in the N/A values with the average using
    df_new = pd.DataFrame(df['year'], columns=['year'], index=df.index)
    for col in df_values.columns:
        df_replace = df_values[col]
        df_replace.name = col
        df_replace = df_replace.fillna(averages)

        # NOTE: For some versions of pandas, a DataFrame must be created explicitly before a concat
        # In this case, this object, prior to creation as DataFrame, is created as a Series
        df_replace = pd.DataFrame(df_replace, columns=[col], index=df_new.index)

        df_new = pd.concat([df_new, df_replace], axis=1, join_axes=[df_values.index])

    # Pick the first, arbitrarily, and then try to beat it
    best_col = columns[0]
    best_diff = abs(df_new[columns[0]] - averages).sum()
    for col in columns:
        diff = abs(df_new[columns[0]] - averages).sum()
        if diff < best_diff:
            best_diff = diff
            best_col = col

    # NOTE: For some versions of pandas, a DataFrame must be created explicitly before a concat
    # In this case, this object, prior to creation as DataFrame, is created as a Series
    df_averages = averages
    #df_averages.name = 'Average ' + datatype + ' across all models'
    df_averages.name = 'average'
    df_averages = pd.DataFrame(df_averages, columns=[df_averages.name], index=df_new.index)

    df_closest_fit = df_new
    df_closest_fit = pd.concat([df_closest_fit, df_averages], axis=1, join_axes=[df_new.index])
    return df_closest_fit

# This function creates a data frame that also includes the 'average' of all the other data
def create_dataframes(filename, datatype, log):
    df = None
    df_closest_fit = None
    try:
        # Read a tab delimited file.
        df = pd.read_table(filename, engine='c', lineterminator='\n', na_values=[''])

        # NOTE: This merges historic with future, but this is likely uncessary and may even be wrong.
        # However, this done merely for convenience.  Please remember to adjust this later.  It will still
        # be important to format the data frame column labels properly, and the correct method may be to
        # create seperate data frames with adjusted column labels.
        #df = merge_columns(df)

        # Get the data frame that is the closest fit (may not be the best) based upon the averages of the value columns
        # in the data frame
        df_closest_fit = get_closest_fit(df, datatype)

    except IOError as ioe:
        if log:
            logging.error(str(ioe))
        return None

    return df_closest_fit

def find_avg_dataframe(df, log=None, value_vars=list()):
    try:
        avg_col = None
        for col in df.columns:
            if 'Average' in str(col):
                avg_col = col
        if avg_col != None:
            df_avg = pd.melt(df, id_vars=['year'], value_vars=[avg_col])
            if len(value_vars) == 0:
                all_columns = list()
                for col in df.columns:
                    all_columns.append(col)
                all_columns.remove(avg_col)
                all_columns.remove('year')
                value_vars = all_columns
            else:
                if avg_col in value_vars:
                    value_vars.remove(avg_col)

            df_lng = pd.melt(df, id_vars=['year'], value_vars=value_vars)
            return df_avg, df_lng
    except KeyError as ke:
        if log:
            logging.error(str(ke))
    return pd.DataFrame(), pd.DataFrame()

def get_avg_plot(plot_title, y_label, df, log):
    print('Creating plot for just average dataframe.')
    df_avg, df_lng = find_avg_dataframe(df, None)
    if len(df_avg) == 0:
        print('Could not find average dataframe!')
    else:
        print(df_avg)
    plot = ggplot(aes(x='year', y='value', color='variable'), data=df_avg)
    plot += geom_point(data=df_avg)
    plot += ggtitle(plot_title)
    plot += xlab('Year')
    plot += ylab(y_label)

    fig = plot.draw()

    return fig

def create_line_plot(plot_title, y_label, df, log, value_vars=list()):
    #variable_colors = dict()
    #colors = ['red', 'blue', 'green', 'orange', 'yellow', 'purple', 'black', 'cyan']
    #colors_to_hex = { 'red': '#FF0000', 'blue': '#00000FF', 'green': '#00FF00', 'orange': '#CC79A7', 'yellow': '#AAAA00', 'purple': '#AA00AA', 'black': '#FFFFFF', 'cyan': '#00AAFF' }
    #colors_to_col = dict()
    #color_index = 0
    #for col in df.columns:
        #if col != 'year':
            #variable_colors[col] = colors[color_index % len(colors)]
            #colors_to_col[colors[color_index % len(colors)]] = col
            #color_index += 1

    # Transform the columns into id, variable, and values columns, using the year column as the id
    df_lng = None
    try:
        df_aes_basis = pd.melt(df, id_vars=['year'])
        df_lng = pd.melt(df, id_vars=['year'], value_vars=value_vars)
    except KeyError as ke:
        if log:
            logging.error(str(ke))
        return None

    #df_avg, df_lng = find_avg_dataframe(df, log, value_vars)
    #if len(df_avg) == 0 or len(df_lng) == 0:
        #return None
    #color_list = list()
    #for row_index, row in df_lng.iterrows():
    #    color_list.append(variable_colors[row.variable])
    #
    #df_colors = pd.DataFrame(color_list, index=df_lng.index, columns=['color_mapping'])
    #df_lng = pd.concat([df_lng, df_colors], axis=1, join_axes=[df_lng.index])
    #

    plot = ggplot(aes(x='year', y='value', color='variable'), data=df_lng)

    #plot.add_to_legend(legend_type='color', legend_dict=colors_to_col)

    #print plot.data._get_numeric_data().columns

    #selected_color_list = list()
    #for col in value_vars:
        #selected_color_list.append(variable_colors[col])

    #plot.manual_color_list = selected_color_list

    #data_assigned_visual_mapping = assign_visual_mapping(data=df_aes_basis, aes=aes(x='year', y='value', color='variable'), gg=plot)
    #print data_assigned_visual_mapping

    plot += geom_line(aes(x='year', y='value', color='variable'), data=df_lng)
    plot += ggtitle(plot_title)
    plot += xlab('Year')
    plot += ylab(y_label)

    fig = plot.draw()

    return fig

def get_range_values(dframe, min_index_value1, max_index_value1, min_index_value2, max_index_value2, index_column):
    '''
    This method retrieves the values within a range between min_index_value and max_index_value indexed by index_key.
    The range is searched first in the dframe1 data frame, then in both dframe1 and dframe2, and then in dframe2.
    Even though the minimum and maximum index values are ordered appropriately, they differences within the ranges may
    be less than zero because the values at the maximum index may be less than the values at the minimum index.
    '''

    # The following lines are to determine if a frame is null or not.
    # The pandas library does not equate a data frame with None unless
    # it is actually none.  Hence, the try...except block
    dframe_is_none = False
    try:
        if dframe == None:
            dframe_is_none = True
    except:
        pass

    # If the minimum values is greater than the maximum value then swap the two.
    if min_index_value1 > max_index_value1:
        temp = min_index_value1
        min_index_value1 = max_index_value1
        max_index_value1 = temp

    if min_index_value2 > max_index_value2:
	temp = min_index_value2
	min_index_value2 = max_index_value2
	max_index_value2 = temp

    # Attempt to find the min and max values in the first data range.
    if not dframe_is_none:
	df1_values = dframe[dframe[index_column] >= min_index_value1]
	df1_values = dframe[dframe[index_column] <= max_index_value1]
	upper_bound_values = df1_values.mean()
	#print(str(df1_mean_values))
    # Attempt to find the min an max values in the second data range.
	df2_values = dframe[dframe[index_column] >= min_index_value2]
	df2_values = dframe[dframe[index_column] <= max_index_value2]
    	lower_bound_values = df2_values.mean()
	#print(str(df2_mean_values))
        diff_values = pd.DataFrame(np.ones((1, len(dframe.columns))), columns=dframe.columns)
        for col in diff_values.columns - [index_column]:
            diff_values[col] = float(upper_bound_values[col]) - float(lower_bound_values[col])

    return diff_values

def get_values_without_extremes(df, x_percent, index_column):
    '''
    This searches through a data frame and removes those values that above and below the specified percentage.
    However, the input data frame would remain intact, except the extremes will be replaced with the average.
    This is only to simplify the accessing of the dataframe later on, as its structure remains the same, but the
    extreme values are removed and replaced with the mean.
    This returns the resulting dataframe.
    '''

    # If the desired percent is 50% then that would leave nothing to search!
    if x_percent > 0.5:
        return None

    data_columns = df.columns - [index_column]
    num_x_percent = int(round(len(df) * x_percent))
    for col in data_columns:
        values_array = np.array(df[col])
        values_array.sort()
        cutoff_min = values_array[num_x_percent]
        cutoff_max = values_array[len(df[col]) - num_x_percent - 1]
        # Replace the values that are less than the minimum cutoff value or greater than the maximum cutoff value
        df[col] = df[col].replace(df[col][df[col] < cutoff_min], df[col].mean())
        df[col] = df[col].replace(df[col][df[col] > cutoff_max], df[col].mean())

    return df

def create_temp_vs_precip_scatter_plot(plot_title, df_temp, df_precip, x_percent, min_year1, max_year1, min_year2, max_year2):
    '''
    This creates a temperature vs. percipitation plot, with extreme values that fall outside the percentile range
    replaced with the mean values of the respective columns.  The values of the plot are derived by taking the difference
    of the values between the min_year and max_year.
    Note, the temperature and precipation data frames are the resulting input from a temperature and a precipitation
    file respectively.
    '''

    year_column = 'year'

    df_temp_diff = get_range_values(df_temp, min_year1, max_year1, min_year2, max_year2, index_column=year_column)
    df_precip_diff = get_range_values(df_precip, min_year1, max_year1, min_year2, max_year2, index_column=year_column)

    # Ensure that the values are legitimate
    df_temp_is_none = False
    try:
        df_temp_is_none = df_temp == None
    except:
        pass

    df_precip_is_none = False
    try:
        df_precip_is_none = df_precip == None
    except:
        pass

    if df_temp_is_none or len(df_temp) <= 0:
        return None
    if df_precip_is_none or len(df_precip) <= 0:
        return None

    df_temp_without_extremes = get_values_without_extremes(df_temp_diff, x_percent, index_column=year_column)
    df_precip_without_extremes = get_values_without_extremes(df_precip_diff, x_percent, index_column=year_column)

    print('Temp diffs: ' + str(df_temp_without_extremes))
    print('Precip diffs: ' + str(df_precip_without_extremes))

    data_columns = df_temp_without_extremes.columns - [year_column]
    data_rows = list()
    for col in data_columns:
        row = [col, df_temp_diff[col][0], df_precip_diff[col][0]]
        data_rows.append(row)

    # Add the median point
    data_rows.append(['median', df_temp_diff.median().median(), df_precip_diff.median().median()])

    x_column = 'Temperature'
    y_column = 'Precipitation'
    color_column = 'Model'

    df_data = pd.DataFrame(data_rows, columns=[color_column, x_column, y_column])

    plot = ggplot(aes(x=x_column, y=y_column, color=color_column), data=df_data)

    # Add scatter plot (geom_point)
    plot += geom_point()

    # The minimum and maximum values may contain multiple columns.  This process keeps the data for each model
    # contained, for the moment.
    xmax = df_temp_without_extremes.max().max()
    xmin = df_temp_without_extremes.min().min()
    ymax = df_precip_without_extremes.max().max()
    ymin = df_precip_without_extremes.min().min()

    print('xmin: ' + str(xmin) + ' xmax: ' + str(xmax) + ' ymin: ' + str(ymin) + ' ymax: ' + str(ymax))

    # Plot a bounding rectangle that defines the maximum and minimum differences, excluding the extreme values.
    plot += geom_rect(aes(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, fill='#ff0000', alpha=0.005))
    plot += geom_vline(aes(x=xmin, ymin=ymin, ymax=ymax, linetype='solid'))
    plot += geom_vline(aes(x=xmax, ymin=ymin, ymax=ymax, linetype='solid'))
    plot += geom_hline(aes(xmin=xmin, xmax=xmax, y=ymin, linetype='solid'))
    plot += geom_hline(aes(xmin=xmin, xmax=xmax, y=ymax, linetype='solid'))

    # Set up plot details
    plot += ggtitle(plot_title)
    plot += xlab(x_column + ' Farenheit')
    plot += ylab(y_column + ' Millimeters')

    fig = plot.draw()

    return fig
