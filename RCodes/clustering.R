## 载入需要的包
library(car)
library(cluster)
library(mclust)
library(NbClust)
library(tidyverse)


AXES = list(
  "Plain" = c(1, 0, 0),
  "Medium" = c(0, 1, 0),
  "High" = c(0, 0, 1)
)
PROFILES = c("Plain", "Medium", "High")
ROOT = "F:/Documents/Li/Master'sThesis/Data"
PLOT_DIR = paste(ROOT, "Plots", sep = "/")


## Import and filter data
filter_data <- function(races_filter='all',
                        result_type='SC',
                        limit=3){
  # The value of 'races_filter' can only be one of 'all'(default), 
  # 'grand_tour', 'other_multi', 'all_multi', and 'single'
  cyclist_meta_dir <- paste(ROOT, "Cyclist_Meta", sep = "/")
  path <- paste0(
    cyclist_meta_dir, 
    paste("/cyclist_meta_merged", races_filter, str_to_upper(result_type), 
          sep = '_'), 
    ".csv"
    )
  raw_data <- read_csv(path)
  if (result_type == 'SC'){
    filtered_data <- dplyr::filter(
    raw_data,
    `Plain: Num` >= limit & `Medium: Num` >= limit & `High: Num` >= limit
    )
  }
  else{
    filtered_data <- raw_data
  }
  save.image()
  return(filtered_data)
}
all_sc_fltrd <- filter_data()
grand_sc_fltrd <- filter_data(races_filter = 'grand_tour')
other_multi_fltrd <- filter_data(races_filter = 'other_multi')
all_multi_fltrd <- filter_data(races_filter = 'all_multi')
single_fltrd <- filter_data(races_filter = 'single')


## 计算两个给定向量的余弦相似度
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


# k-means聚类
kmclustering <- function(){
  d <- cyclist_meta_sc_filtered[, c(
    "Similarity of Plain Avg Rank",
    "Similarity of Medium Avg Rank",
    "Similarity of High Avg Rank")]
  km_sim_avg_rank <- kmeans(d, centers = 3, nstart = 3, trace = TRUE)
  km_sim_avg_rank <- append(km_sim_avg_rank, list(data = d))
  return(km_sim_avg_rank)
}

# km_sim_avg_rank <- kmclustering()
