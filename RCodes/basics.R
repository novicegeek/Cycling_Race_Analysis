require(stringr)
require(tidyverse)  # for readr::read_csv, dplyr::filter()


AXES = list(
  "Plain" = c(1, 0, 0),
  "Medium" = c(0, 1, 0),
  "High" = c(0, 0, 1)
)
PROFILES = c("Plain", "Medium", "High")
RELOAD = FALSE
ROOT = "F:/Documents/Li/Master'sThesis/Data"
PLOT_DIR = paste(ROOT, "Plots", sep = "/")


## Automatically add aggregated information to existing data
add_aggr <- function(input, ref, func){
  input <- add_order(input)
  if (!"aggregate by norm cluster" %in% names(input)){
    aranks <- aggregate(input$data$ranks[, 2:4],
                        by = list(ref$data$ranks$cluster),
                        FUN = func)
    amedian <- aggregate(input$data$speed2median[, 2:4],
                         by = list(ref$data$speed2median$cluster),
                         FUN = func)
    input$`aggregate by norm cluster` <- list('ranks' = aranks,
                                              'speed2median' = amedian)
  }
  if (!"aggregate order by norm cluster" %in% names(input)){
    aoranks <- aggregate(input$data$ranks[,c("Plain order", "Medium order", "High order")],
                         by = list(ref$data$ranks$cluster),
                         FUN = func)
    aomedian <- aggregate(input$data$speed2median[, c("Plain order", "Medium order", "High order")],
                          by = list(ref$data$speed2median$cluster),
                          FUN = func)
    input$`aggregate order by norm cluster` <- list('ranks' = aoranks,
                                                    'speed2median' = aomedian)
  }
  return(input)
}


add_order <- function(input){
  if (!"Plain order" %in% colnames(input$data$ranks)){
    for (i in 1:nrow(input$data$ranks))
      input$data$ranks[i, c("Plain order", "Medium order", "High order")] <- 
        rank(input$data$ranks[i, 2:4])
  }
  if (!"Plain order" %in% colnames(input$data$speed2median)){
    for (i in 1:nrow(input$data$speed2median))
      input$data$speed2median[i, c("Plain order", "Medium order", "High order")] <- 
        rank(input$data$speed2median[i, 2:4])
  }
  return(input)
}


all_capitalize <- function(str, split = '_', sep = ' '){
  if (class(str) != 'character')
    stop("Input is not a string.")
  else{
    parts <- c()
    for (part in strsplit(str, split = split)[[1]])
      parts <- append(parts, str_to_title(part))
    paste(parts, collapse = sep)
  }
}


## Calculate the cosine similarity between two vectors
cal_cos_similarity <- function(vec1, vec2){
  if (class(vec1) != "numeric"){
    print("Vector 1 is not a numeric vector")
  }
  else if(class(vec2) != "numeric"){
    print("Vector 2 is not a numeric vector")
  }
  else if (length(vec1) != length(vec2)){
    print("The vectors are not of equal length")
  }
  else{
    return(sum(vec1*vec2)/(sqrt(sum(vec1^2))*sqrt(sum(vec2^2))))
  }
}


## 计算每名车手的成绩和不同地形的余弦相似度
add_cos_similarity <- function(dataframe){
  for (field in c("Avg Rank", "Avg Speed Rel to Median")){
    old_col_names <- c()
    
    for (profile in PROFILES){
      old_col_names <- append(old_col_names, paste(profile, field, sep = ": "))
    }
    
    for (rowname in rownames(cyclist_meta_sc_filtered)){
      current_row <- cyclist_meta_sc_filtered[rowname, ]
      current_vector <- as.numeric(current_row[old_col_names])
      magnitude <- sqrt(sum(current_vector^2))
      cyclist_meta_sc_filtered[rowname, paste("Magnitude of", field)] <- magnitude
      
      for (profile in PROFILES){
        new_col_name <- paste("Similarity of", profile, field)
        cyclist_meta_sc_filtered[rowname, new_col_name] <- 
          cal_cos_similarity(current_vector, AXES[[profile]])
      }
    } 
  }
  return(cyclist_meta_sc_filtered)
}
# cyclist_meta_sc_filtered <- filter_data()
# cyclist_meta_sc_filtered <- add_cos_similarity(cyclist_meta_sc_filtered)


## Generate new headers for subsetting dataframe
cols_paste <- function(x){
  new_cols <- c()
  for (profile in PROFILES){
    new_cols <- append(new_cols, paste(profile, x, sep = ': '))
  }
  return(new_cols)
}


## Import and filter data
filter_data <- function(input,
                        races_filter='all',
                        result_type='SC',
                        stage_class='profile',
                        cols=c(),
                        limit=3){
  # The value of 'races_filter' can only be one of 'all'(default), 
  # 'grand_tour', 'other_multi', 'all_multi', and 'single'
  if (class(input) == 'character')
    filtered_data <- read_csv(input)
  else if ('data.frame' %in% class(input))
    filtered_data <- input
  # Generate to names of the columns to filter by
  if (length(cols) == 0){
    if (result_type == 'SC'){
      if (stage_class == 'profile')
        for (profile in PROFILES)
          cols <- append(cols, paste(profile, 'Num', sep = ': '))
      else
        for (col_name in colnames(raw_data))
          if ('Num' %in% col_name & (!'Total' %in% col_name))
            cols <- append(cols, col_name)
    }
    else if (races_filter == 'all')
      cols <- 'Total: Num'
    else{
      prefix <- all_capitalize(races_filter)
      cols <- paste(prefix, 'Num', sep = ': ')
    }
  }
  # Filter by every column in cols with the lower limit
  for (col in cols){
    filtered_data <- filtered_data[c(filtered_data[col] >= limit), ]
  }
  save.image()
  return(filtered_data)
}
if (RELOAD){
  # all_sc_fltrd <- filter_data()
  # grand_sc_fltrd <- filter_data(races_filter = 'grand_tour')
  # other_multi_sc_fltrd <- filter_data(races_filter = 'other_multi')
  # all_multi_sc_fltrd <- filter_data(races_filter = 'all_multi')
  # single_sc_fltrd <- filter_data(races_filter = 'single')
}


vector_magnitude <- function(vec){
  if (class(vec) != "numeric"){
    print("Invalid input.")
    return()
  }
  else sqrt(sum(vec^2))
}


vector_normalize <- function(vec){
  if (class(vec) == "numeric"){
    magnitude <- vector_magnitude(vec)
    if (magnitude == 0){
      print("The input vector is zero.")
      return(vec)
    }
    else vec/magnitude
  }
  else{
    print("Invalid input.")
    return()
  }
}