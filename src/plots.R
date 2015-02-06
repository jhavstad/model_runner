# This function gets a row from the table based upon the value of index
get_row_by_year = function(table, index) {
  len = length(table[,2])
  index = toString(index)
  for (i in 1 : len) { 
    row = table[i,]
    if (row[1] == index) {
      return(row)
    }
  }
  # NA if the row was not found
  return(NA)
}

# This function performs imputation on the values in the table,
# replacing any NULL or NA values with the averages calculated
# from the rest of the non-NA value in the column
imputation_table = function(table) {
  nrows = nrow(table)
  ncols = ncol(table)
  for (j in 2 : ncols) {
    table[,j] = imputation_col(table[,j], nrows)
  }
  return(table)
}

# This function iterates through all the columns to perform
# imputation on each column
imputation_col = function(col, nrows) {
  sum = 0
  num_avail_values = 0
  for (i in 1 : nrows) {
    if (!is.na(col[i])) {
      sum = sum + col[i]
      num_avail_values = num_avail_values + 1
    }
  }
  average = sum / num_avail_values
  for (i in 1 : nrows) {
    if (is.na(col[i])) {
      col[i] = average
    }
  }
  return(col)
}

# This function performs imputation on a single row by
# calculating the average value from the rest of the 
# columns in the row
imputation_row = function(row, ncols) {
  sum = 0
  num_avail_cols = 0
  for (i in 2 : ncols) {
    if (!is.na(row[,i])) {
      sum = sum + row[,i]
      num_avail_cols = num_avail_cols + 1
    }
  }
  average = sum / num_avail_cols
  for (i in 2 : ncols) {
    if (is.na(row[,i])) {
      row[i] = average
    }
  }
  return(row)
}

# This function calculates the euclidan distance between two points
dist = function(pt1, pt2) {
  x_diff_squared = (pt1[1] - pt2[1]) ** 2
  y_diff_squared = (pt1[2] - pt2[2]) ** 2
  return ((x_diff_squared + y_diff_squared) ** 0.5)
}

# This function determines which values in a row are closest to,
# or with the minimum distance to, the quantile values
get_min_values = function(x_table, y_table, x_quantile, y_quantile) {
  if (ncol(x_table) != ncol(y_table)) {
    return(NULL)
  }
  ncols = ncol(x_table)
  dist_pts = c(x_quantile[1], y_quantile[1], x_quantile[2], y_quantile[1], x_quantile[1], y_quantile[2], x_quantile[1], y_quantile[2])
  min_values = c(NA, NA, NA, NA, NA, NA, NA, NA)
  for (i in 2 : ncols) {
    model_pt = c(x_table[,i], y_table[,i])
    for (j in seq(1,8,2)) {
      quantile_pt = c(dist_pts[j], dist_pts[j+1])
      model_quantile_dist = dist(model_pt, quantile_pt)
      if (is.na(min_values[j]) || 
            is.nan(min_values[j]) ||
            is.null(min_values[j]) ||
            model_quantile_dist < min_values[j]) {
        min_values[j] = model_quantile_dist
        min_values[j+1] = i
      }
    }
  }
  return(min_values)
}

# This function gets the station values for the start year, end year,
# and the extreme values
get_station_values = function(temp_filename, precip_filename, hist_year, future_year) {
  temp = read.table(file=temp_filename, header=TRUE, sep="\t")
  precip = read.table(file=precip_filename, header=TRUE, sep="\t")
  
  temp = imputation_table(temp)
  precip = imputation_table(precip)
  
  # Retrieve the number of columns in the precipitation and temperature
  # tables
  ncols.temp = ncol(temp)
  ncols.precip = ncol(precip)
  
  # Validate the data
  # 1: The number of columns in the precipitation and temperature
  # tables should match up
  if (ncols.temp != ncols.precip) {
    return(NA)
  }
  
  # Retrieve the number of row in the precipitation and temperature
  # tables
  nrows.temp = nrow(temp)
  nrows.precip = nrow(precip)
  
  # Validate the data
  # 2: The number of rows in the precipitation and temperature
  # tables should match up
  if (nrows.temp != nrows.precip) {
    return(NA)
  }
  
  # Retrieve the requested historical and future data from the
  # temperature table
  # Validate the data
  # 3: Each call to get_row_by_year implicitly calls an
  # imputation function to replace bad values with the mean value
  # for each model
  temp.hist = get_row_by_year(temp, hist_year)
  temp.future = get_row_by_year(temp, future_year)
  
  # Validate the data
  # 4: Replace bad values in a row with the mean value across
  # all models for the historical and future years
  temp.hist = imputation_row(temp.hist, ncols.temp)
  temp.future = imputation_row(temp.future, ncols.temp)
  
  # Retrieve the requested historical and future data from the
  # precipitation table
  # Validate the data
  # 5: Each call to get_row_by_year implicitly calls an
  # imputation function to replace bad values with the mean value
  # for each model
  precip.hist = get_row_by_year(precip, hist_year)
  precip.future = get_row_by_year(precip, future_year)
  
  # Validate the data
  # 6: Replace bad values in a row with the mean value across
  # all models for the historical and future years
  precip.hist = imputation_row(precip.hist, ncols.precip)
  precip.future = imputation_row(precip.future, ncols.precip)
  
  # Calculate the differences of the temperature and preciptation values
  temp.diff = temp.future - temp.hist
  precip.diff = precip.future - precip.hist
  
  # Calculate the quantile values for the lower and upper 10% values
  temp.quantile = quantile(temp.diff, c(.10, .90), na.rm=TRUE)
  precip.quantile = quantile(precip.diff, c(.10, .90), na.rm=TRUE)
  
  # Bind the column names and column values to their own columns
  # This will provide a more straight forward way to access
  # the numerical values
  temp.quantile = cbind(temp.quantile)
  precip.quantile = cbind(precip.quantile)
  
  # Get the models that have the minimum distance to the 4 extremes
  min_values = get_min_values(temp.diff, precip.diff, temp.quantile, precip.quantile)
  
  return(list(temp.diff, precip.diff, temp.quantile, precip.quantile, min_values))
}

get_station_plot = function(temp_values, precip_values, min_values, station_name) {
  plot(x=precip_values, y=temp_values, pch=20, col="black", title=station_name)
  
}

process_stations = function(temp_filenames, precip_filenames, start_year, end_year) {
  num_temp_files = length(temp_filenames)
  num_precip_files = length(precip_filenames)
  if (num_temp_files != num_precip_files) {
    return(NA)
  }
  
  num_files = num_temp_files
  
  station_info = strsplit(temp_filename, "_")
  station_name = station_info[[1]][1]
  
  for (i in 1 : num_files) {
    temp_filename = temp_filenames[i]
    precip_filename = precip_filenames[i]
    
    station_values = get_station_values(temp_filename, precip_filename, start_year, end_year)
    
    temp.values = station_values[1]
    precip.values = station_values[2]
    temp.quantile = station_values[3]
    precip.quantile = station_values[4]
    min_values = stations_values[5]
    
    get_station_plot(temp.values, precip.values, temp.quantile, precip.quantile, min_values, station_name)
  }
}