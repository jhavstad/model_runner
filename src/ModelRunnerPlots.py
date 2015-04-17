from ggplot import *
import pandas as pd
import logging
import numpy as np

import matplotlib.pyplot as plt

def get_model(name):
    try:
        return name[0:name.index('_')]
    except:
        pass
    return name

def get_era(name):
    try:
        firstIndex = name.index('_')
        return name[firstIndex+1:name.index('_', firstIndex+1)]
    except:
        pass
    return name

def get_col_intersection(df1, df2):
    df1_columns = df1.columns
    df2_columns = df2.columns
    intersection_columns = df1_columns
    for col in intersection_columns:
        if col not in df2_columns:
            intersection_columns.remove(col)
    return intersection_columns

def get_model_diffs(df1, df2, historic_start_year, historic_end_year, future_start_year, future_end_year, index_column):
    '''
    This function is really just an effort to organize the incoming data frames
    into a format so that the historic value range can be subtracted from the
    the future value range.  This function will take the mean of the values 
    within each range, subtract them and return the result.  It will return
    the result for both data frames.  The input data frames represent the
    X and Y plot axes respectiviely. 
    The output will be a dictionary with elements in an np.array format, 
    with one array for each one.
    '''
    # Attempt to get the columns that are common between the two data frames. 
    intersection_columns = get_col_intersection(df1, df2)
  
    # Create a listing of all the models that are common between the two data
    # frames (provided above) and then filter out those that do not have 
    # both a future and historic values.

    models = dict()
    historic_value = 'historical'
    historic_key = 'historic'
    future_key = 'future'
    for col in intersection_columns:
        model = get_model(col)
        era = get_era(col)
        if model not in models:
            models[model] = dict()
        #print("era: " + era)
        if era == historic_value:
            models[model][historic_key] = col
        else:
            models[model][future_key] = col

    # Return the differences between the historic and future values
    # for the two data frames. 
    df1_diffs = _get_model_diffs(df1, models, historic_start_year, historic_end_year, future_start_year, future_end_year, historic_value, historic_key, future_key, index_column)

    df2_diffs = _get_model_diffs(df2, models, historic_start_year, historic_end_year, future_start_year, future_end_year, historic_value, historic_key, future_key, index_column)

    return (df1_diffs, df2_diffs)

def _get_model_diffs(df, models, historic_start_year, historic_end_year, future_start_year, future_end_year, historic_value, historic_key, future_key, index_column):
    #print("Retrieving values for data frame: " + str(models))
    #print("Historic interval (years): " + str(historic_end_year - historic_start_year))
    #print("Future interval (years): " + str(future_end_year - future_start_year))
    
    output = dict()
    for model in models:
        #print("Model in models: " + str(models[model]))
        if historic_key in models[model] and future_key in models[model]:
	    #print("Calculating difference for model: " + model);
	    df_historic = models[model][historic_key]
            df_future = models[model][future_key]
            df_historic = df[df_historic]
            df_future = df[df_future]
            df_historic = df_historic[df[index_column] >= historic_start_year]
            df_historic = df_historic[df[index_column] <= historic_end_year]
            df_future = df_future[df[index_column] >= future_start_year]
            df_future = df_future[df[index_column] <= future_end_year]
            df_historic_values = df_historic.values.flatten()
            df_future_values = df_future.values.flatten()
	    #print(str(len(df_future_values)))
	    #print(str(len(df_historic_values)))
            output[model] = df_future_values - df_historic_values

    return output    

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
            if 'average' in str(col):
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
            
            print("Found average dataframe")
	    
            return df_avg, df_lng
    except KeyError as ke:
        if log:
            logging.error(str(ke))
        else:
            print("Could not find average dataframe")
    return pd.DataFrame(), pd.DataFrame()

def get_avg_plot(plot_title, y_label, df, log):
    #print('Creating plot for just average dataframe.')
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

# NOTE: This is deprecated
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
    
def get_data_without_extremes(data, percent):
    if percent > 0.5:
        return None

    data_without_extremes = dict()
    for model in data:
	#print("Reading model " + model)
    	index_min = int(round(float(len(data[model])) * percent)) - 1
        index_max = len(data[model]) - index_min
	#print("Index min: " + str(index_min))
	#print("Index max: " + str(index_max))
        values_array = np.array(data[model])
        values_array.sort()
        cutoff_min = values_array[index_min]
        cutoff_max = values_array[index_max]
	#print("Cutoff min: " + str(cutoff_min))
	#print("Cutoff max: " + str(cutoff_max))
	data_without_extremes[model] = data[model].copy()
	# This is an exclusive interval at or below the min_index, or
	# anything at or above the max_index is excluded
	data_model_mean = data[model].mean()
	#print("The model mean is: " + str(data_model_mean))
        for i in range(len(data[model])):
            if data[model][i] < cutoff_min:
		#print("Found a value at the minimum cutoff value")
                data_without_extremes[model][i] = data_model_mean
		#print("Value at index " + str(i) + " is " + str(data_without_extremes[model][i]))
		#print("Original value is " + str(data[model][i]))
            if data[model][i] > cutoff_max:
		#print("Found a value at the maximum cutoff value")
                data_without_extremes[model][i] = data_model_mean
		#print("Value at index " + str(i) + " is " + str(data_without_extremes[model][i]))
		#print("Original value is " + str(data[model][i]))
    return data_without_extremes

# This function is deprecated
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

def test_func():
    print("Testing - is this here")

def create_temp_vs_precip_scatter_plot_r2(plot_title, df_temp, df_precip, x_percent, historic_start_year, historic_end_year, future_start_year, future_end_year):
    '''
    This creates a temperature vs. percipitation plot, with extreme values that fall outside the percentile range
    replaced with the mean values of the respective columns.  The values of the plot are derived by taking the difference
    of the values between the min_year and max_year.
    Note, the temperature and precipation data frames are the resulting input from a temperature and a precipitation
    file respectively.
    '''

      

    #temp_diffs_without_extremes = get_data_without_extremes(temp_diffs, x_percent)
    #temp_diffs_min_max = np.percentile(temp_diffs.values, [x_percent * 100, 100 - x_percent * 100])
    #precip_diffs_min_max = np.percentil(precip_diffs.values, [x_perecent * 100, 100 - x_percent * 100])
    #precip_diffs_without_extremes = get_data_without_extremes(precip_diffs, x_percent)
    
    data_rows = list()
    #model_medians = [np.ones(len(temp_diffs)), np.ones(len(precip_diffs))]
    model_index = 0

    for model in temp_diffs:
	row = [model, temp_diffs[model], precip_diffs[model]]
	data_rows.append(row)

    df_data = pd.DataFrame(data_rows)
    print(df_data.head())
    
    #for model in temp_diffs:
        # So the calculation should be for all the years for all the models
        # The current calculation is taking the average
    	#median_index = round(float(len(temp_diffs[model])) / 2.0)
        
	#model_column = np.array([model for i in range(len(temp_diffs[model]))])
        #print(model_column)
        #table = [model_column, temp_diffs[model], precip_diffs[model]]

        #print(table)
	#rows = list()
		
        
        #data_rows.append(table[0:10])
	#temp_median = temp_diffs[model][median_index]
        #precip_median = precip_diffs[model][median_index]
      
        #model_medians[0][model_index] = temp_median
        #model_medians[1][model_index] = precip_median
        #model_index += 1

    #median_index = round(float(len(temp_diffs)) / 2.0)
    #model_medians[0].sort()
    #model_medians[1].sort()
    
    #data_rows.append(['median', model_medians[0][median_index], model_medians[1][median_index]])
    #print(table[0:10])
    
    x_column = 'Temperature'
    y_column = 'Precipitation'
    color_column = 'Model'

    #df_data = pd.DataFrame(pd.concat([df_temp, df_precip]), columns=[color_column, x_column, y_column])

    #df_data = pd.melt(df_data, id_vars=["Model"], value_vars=["Temperature", "Precipitation"])

    #print(df_data.columns)

    #print(df_data["Model"].head())

    plot = ggplot(aes(x=x_column, y=y_column), data=df_data)

    plot += geom_point()

    xmax = None
    xmin = None
    ymax = None
    ymin = None

    xmin_candidates = []
    xmax_candidates = []
    ymin_candidates = []
    ymax_candidates = []

    for model in temp_diffs:
	# Copy data into alternate data frames so that the values may 
	# be changed without affecting the original data frames
        temp_values_sorted = temp_diffs[model]
        precip_values_sorted = precip_diffs[model]
	temp_values_sorted.sort()
	precip_values_sorted.sort()
        percentile_min = x_percent * 100
	percentile_max = 100 - x_percent * 100
	x_boundaries = np.percentile(temp_diffs[model], [percentile_min, percentile_max])
	y_boundaries = np.percentile(precip_diffs[model], [percentile_min, percentile_max])
	print(x_boundaries)
	print(y_boundaries)
	if not np.isnan(x_boundaries[0]):
	    xmin_candidates.append(x_boundaries[0])
	if not np.isnan(x_boundaries[1]):
	    xmax_candidates.append(x_boundaries[1])
	if not np.isnan(y_boundaries[0]):
	    ymin_candidates.append(y_boundaries[0])
	if not np.isnan(y_boundaries[1]):
	    ymax_candidates.append(y_boundaries[1])
        #first_index = 0
        #last_index = len(temp_values_sorted) - 1
        
        #if xmax == None or xmax < temp_values_sorted[last_index]:
            #xmax = temp_values_sorted[last_index]

        #if xmin == None or xmin < temp_values_sorted[first_index]:
            #xmin = temp_values_sorted[first_index]

        #if ymax == None or ymax < precip_values_sorted[last_index]:
            #ymax = precip_values_sorted[last_index]

        #if ymin == None or ymin < precip_values_sorted[last_index]:
            #ymin = precip_values_sorted[first_index]

    x_max = max(xmax_candidates)
    x_min = min(xmin_candidates)
    y_max = max(ymax_candidates)
    y_min = min(ymin_candidates)

    # Now, attempt to find the points that are closest to the xmin, xmax, ymin, ymax
    

    #print("Median temp: " + str(model_medians[0][median_index]))
    #print("Median precip: " + str(model_medians[1][median_index]))
    print("Min temp: " + str(x_min))
    print("Max temp: " + str(x_max))
    print("Min precip: " + str(y_min))
    print("Max precip: " + str(y_max))
            
    plot += geom_rect(aes(xmin=x_min, xmax=x_max, ymin=y_min, ymax=y_max, fill='#00ff00', alpha=0.05))
    plot += geom_vline(aes(xintercept=x_min, ymin=y_min, ymax=y_max, color="#000000", linetype='solid'))
    plot += geom_vline(aes(xintercept=x_max, ymin=y_min, ymax=y_max, color="#000000", linetype='solid'))
    plot += geom_hline(aes(xmin=x_min, xmax=x_max, yintercept=y_min, color="#000000", linetype='solid'))
    plot += geom_hline(aes(xmin=x_min, xmax=x_max, yintercept=y_max, color="#000000", linetype='solid'))

    # Set up plot details
    plot += ggtitle(plot_title)
    plot += xlab(x_column + ' Farenheit')
    plot += ylab('Chance of ' + y_column)

    fig = plot.draw()

    return fig

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

    #print('Temp diffs: ' + str(df_temp_without_extremes))
    #print('Precip diffs: ' + str(df_precip_without_extremes))

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

    #print('xmin: ' + str(xmin) + ' xmax: ' + str(xmax) + ' ymin: ' + str(ymin) + ' ymax: ' + str(ymax))

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
