## 载入需要的包
require(car)
require(tidyverse)
source('basics.R')


# ## 检验正态性
# # 绘制并导出直方图至Plots文件夹
# for (profile in c("Plain", "Medium", "High")){
#   while (!"windows" %in% names(dev.list())){
#     dev.new()
#   }
#   for (field in c("Avg Rank", "Avg Speed Rel to Median")){
#     col_name <- paste(profile, field, sep = ": ")
#     hist(
#       cyclist_meta_sc_filtered[[col_name]],
#       right = FALSE,
#       main = paste("Histogram of", col_name),
#       xlab = col_name
#     )
#     savePlot(
#       filename = paste(
#         PLOT_DIR, 
#         paste(tolower(c("hist", profile, strsplit(field, " ")[[1]])), 
#               collapse = "_"),
#         sep = "/"
#       ),
#       type = 'jpg'
#     )
#   }
#   dev.off()
# }
# # Q-Q Plot
# for (profile in c("Plain", "Medium", "High")){
#   while (!"windows" %in% names(dev.list())){
#     dev.new()
#   }
#   for (field in c("Avg Rank", "Avg Speed Rel to Median")){
#     col_name <- paste(profile, field, sep = ": ")
#     qqPlot(
#       cyclist_meta_sc_filtered[[col_name]],
#       main = paste("Q-Q Plot of", col_name),
#       xlab = "Theoretical Norm Quantiles",
#       ylab = field,
#       cex = 0.5, lwd = 1, pch = 20
#     )
#     savePlot(
#       filename = paste(
#         PLOT_DIR, 
#         paste(tolower(c("qq", profile, strsplit(field, " ")[[1]])), 
#               collapse = "_"),
#         sep = "/"
#       ),
#       type = 'jpg'
#     )
#   }
#   dev.off()
# }
# # 统计检验
# for (profile in c("Plain", "Medium", "High")){
#   for (field in c("Avg Rank", "Avg Speed Rel to Median")){
#     col_name <- paste(profile, field, sep = ": ")
#     # Kolmogorov-Smirnov test for normality
#     assign(
#       paste(tolower(c("ks", profile, strsplit(field, " ")[[1]])), 
#             collapse = "_"),
#       ks.test(cyclist_meta_sc_filtered[[col_name]], "pnorm")
#       )
#     # Shapiro-Wilk normality test
#     assign(
#       paste(tolower(c("sw", profile, strsplit(field, " ")[[1]])), 
#             collapse = "_"),
#       shapiro.test(cyclist_meta_sc_filtered[[col_name]])
#     )
#   }
# }
# save.image()
# 
# 
# ## 检验不同地形之间的表现是否存在显著差异
# # Kruskal-Wallis Test
# for (field in c("Avg Rank", "Avg Speed Rel to Median")){
#   col_names <- c()
#   for (profile in c("Plain", "Medium", "High")){
#     col_names <- append(col_names, paste(profile, field, sep = ": "))
#   }
#   # Kruskal-Wallis test is used due to non-normality of the data
#   assign(
#     paste(c("kw", tolower(strsplit(field, " ")[[1]])), collapse = "_"), 
#     kruskal.test(cyclist_meta_sc_filtered[col_names])
#     )
# }
# Friedman Test
# friedman <- function(){
#   avg_ranks <- as.matrix(cyclist_meta_sc_filtered[, c(
#     "Plain: Avg Rank", "Medium: Avg Rank", "High: Avg Rank"
#   )])
#   friedman_avg_rank <- friedman.test(avg_ranks)
#   return(friedman_avg_rank)
# }
# friedman_avg_rank <- friedman()


## Test if any difference in GC between different clusters
get_cluster_gc_info <- function(input, ref, 
                                cluster_by = c("ranks", "speed2median"),
                                method){
  if (class(ref) == "list"){
    by <- switch(match.arg(cluster_by), "ranks" = 1L, "speed2median" = 2L)
    if (by == 1L) cluster <- ref$data$ranks$cluster
    else if (by == 2L) cluster <- ref$data$speed2median$cluster
  }
  else if ("data.frame" %in% class(ref))
    cluster <- ref$cluster
  else if (class(ref) %in% c("integer", "numeric", "character", "factor"))
    cluster <- ref
  else
    stop("Invalid reference data.")
  
  # Calculate valid number of individuals and averages
  num_split <- split(input$`Grand Tour: Num`, cluster)
  ranks_split <- split(input$`Grand Tour: Avg Rank`, cluster)
  median_split <- split(input$`Grand Tour: Avg Avg Speed Rel to Median`, cluster)
  general_info <- list('cluster by' = cluster_by, 
                       'clustering method' = method,
                       'total n' = 0L)
  total_n <- 0L
  for (name in names(ranks_split)){
    n <- length(num_split[[name]])
    total_n <- total_n + n
    mean_rank <- mean(ranks_split[[name]])
    mean_median <- mean(median_split[[name]])
    general_info[[name]] <- list('n' = n,
                                 'mean avg rank' = mean_rank,
                                 'mean avg avg speed rel to median' = mean_median)
  }
  general_info$`total n` <- total_n
  
  # Test cluster-wise normality
  ranks_sw_test <- lapply(ranks_split, shapiro.test)
  median_sw_test <- lapply(median_split, shapiro.test)
  
  list('general info' = general_info,
       'normality' = list('ranks' = ranks_sw_test, 'speed2median' = median_sw_test))
}
ref_matchrow <- match(grand_gc_fltrd$ID, grand_sc_normalize_kmeans$data$ranks$ID, 
                      nomatch = FALSE)
ref <- grand_sc_normalize_kmeans$data$ranks$cluster[ref_matchrow]
grand_gc_aggregate <- get_cluster_gc_info(input = grand_gc_fltrd,
                                          ref = ref,
                                          cluster_by = "ranks",
                                          method = "kmeans")
