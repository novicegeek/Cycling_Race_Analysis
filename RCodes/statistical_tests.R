## 载入需要的包
library(car)
library(tidyverse)


AXES = list(
  "Plain" = c(1, 0, 0),
  "Medium" = c(0, 1, 0),
  "High" = c(0, 0, 1)
)
PROFILES = c("Plain", "Medium", "High")
ROOT = "F:/Documents/Li/Master'sThesis/Data"
PLOT_DIR = paste(ROOT, "Plots", sep = "/")


## 筛取数据
filter_data <- function(){
  cyclist_meta_dir <- paste(
    ROOT, "Cyclist_Meta", sep = "/"
  )
  cyclist_meta_path_sc <- paste(
    cyclist_meta_dir, "cyclist_meta_merged_SC.csv", sep = "/"
  )
  cyclist_meta_sc <- readr::read_csv(cyclist_meta_path_sc)
  cyclist_meta_sc_filtered <- dplyr::filter(
    cyclist_meta_sc,
    `Plain: Num` >= 3 & `Medium: Num` >=3 & `High: Num` >= 3
  )
  save.image()
  return(cyclist_meta_sc_filtered)
}


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
friedman <- function(){
  avg_ranks <- as.matrix(cyclist_meta_sc_filtered[, c(
    "Plain: Avg Rank", "Medium: Avg Rank", "High: Avg Rank"
  )])
  friedman_avg_rank <- friedman.test(avg_ranks)
  return(friedman_avg_rank)
}
friedman_avg_rank <- friedman()