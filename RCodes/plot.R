source('basics.R')
require(reshape2)
require(Rmisc)
Sys.setlocale("LC_CTYPE", "US")
SAVE_ROOT = "F:/Documents/Li/Master'sThesis/Data/Plots"


get_melt_info <- function(input,
                          criterion = c("avg", "best"), 
                          stage_class = "profile",
                          races_filter = NULL,
                          var = c("ranks", "speed2median"),
                          ref = NULL){
  if (!'cluster' %in% colnames(input) & is.null(ref))
    stop("No cluster information.")
  else if (!'cluster' %in% colnames(input) & nrow(input) != length(ref))
    stop("The reference clusters must be of the same length as the dataframe.")
  
  criterion <- str_to_title(criterion)
  var <- switch(var, "ranks" = "Rank", "speed2median" = "Avg Speed Rel to Median")
  melt_cols <- c('ID')
  if (stage_class == "profile" & is.null(races_filter)){
    for (profile in PROFILES)
      melt_cols <- append(melt_cols, 
                          paste(profile, paste(criterion, var), sep = ": "))
    var_name <- stage_class
  }
  else if (!is.null(races_filter)){
    races <- all_capitalize(races_filter)
    melt_cols <- append(melt_cols, 
                        paste(races, paste(criterion, var), sep = ": "))
    var_name <- 'races'
  }
  # Extract the columns needed
  if (is.null(ref) & 'cluster' %in% colnames(input))
    to_melt_df <- input[, append(melt_cols, 'cluster')]
  else if (!is.null(ref))
    to_melt_df <- cbind(input[, append('ID', melt_cols)], list('cluster' = ref))
  else stop("No reference clusters information.")
  # Melt
  melt_df <- reshape2::melt(to_melt_df, id.vars = c('ID', 'cluster'),
                            measure.vars = melt_cols[!melt_cols %in% c('ID', 'cluster')], 
                            variable.name = var_name,
                            value.name = 'value')
  
  if (is.null(races_filter))
    return(list('data' = melt_df, 'stage classifying by' = stage_class))
  else
    return(list('data' = melt_df, 'races' = races))
}


auto_plot <- function(data, 
                      var_name = "profile", 
                      is_gc = FALSE,
                      value_name = "value",
                      value_type = c("ranks", "speed2median"),
                      criterion = c("avg", "best"),
                      normalized = FALSE,
                      type = c("bar", "line"), 
                      error_bar = TRUE,
                      file_name,
                      file_type = "png",
                      low_res = NULL,
                      ...){
  arrow_angle = 22.5
  bar_width = 0.5
  expand_coef_global = 1.1
  expand_coef_right = 1.30
  plot_width = 4800L
  plot_height = 3600L
  ytick_limit = 0.05
  ytrunc_limit = 0.1
  if (is.null(low_res)) low_res <- 1
  data_count <- summarySE(data, measurevar = value_name, 
                          groupvars = c('cluster', var_name), na.rm = TRUE)
  if (value_name == "value"){
    if (type == "line" & var_name == "profile" & !is_gc)
      p <- ggplot(data_count, aes(x = profile, y = value, color = cluster,
                            group = cluster), ...) +
        geom_line(position = position_dodge(0.1)) +
        geom_point(position = position_dodge(0.1)) +
        guides(color = guide_legend(title = "类别")) +
        xlab("地形")
    else if (type == "bar"){
      if (var_name == "profile" & !is_gc){
        legends <- factor(data_count[[var_name]], 
                          labels = c("平坦", "普通山地", "高山"))
        data_count$legend <- legends
        p <- 
          ggplot(data_count, aes(x = factor(cluster), y = value, fill = legend)) +
          geom_bar(colour = "black", stat = "identity", position = position_dodge(), 
                   width = bar_width) +
          # guides(colour = FALSE, fill = guide_legend(title = NULL)) +
          scale_fill_manual(values = c("white", "dark gray", "black")) +
          xlab("类别")
      }
      else if (is_gc){
        bar_width <- 0.6 * bar_width
        p <- 
          ggplot(data_count, aes(x = factor(cluster), y = value)) +
          geom_bar(colour = "black", fill = "dark gray", stat = "identity", 
                   position = position_dodge(), width = bar_width) +
          xlab("类别")
      }
    }
  }
  # Add error bar
  if (error_bar)
    p <- p + geom_errorbar(aes(ymin = value, ymax = value + sd),
                           width = 0.4 * bar_width, position = position_dodge(bar_width))
  # Set y-axis title
  ylabel_norm <- if (normalized) "标准化" else ""
  ylabel_pref <- switch(criterion, "avg" = "平均", "best" = "最优")
  ylabel_suff <- switch(value_type, "ranks" = "排名", "speed2median" = "完赛均速与中位数速度之比")
  # Set y-axis attributes: lower limit, breaks
  y_lower_lim <- NULL
  if ((max(data_count[[value_name]]) - min(data_count[[value_name]]))/
           max(data_count[[value_name]]) < ytrunc_limit){
    lower_exp = floor(log10(min(data_count[[value_name]])))
    # intrvl_res = 10^lower_exp
    dis_to_low <- sapply(min(data_count[[value_name]]), 
                         FUN = function(val, exp){
                           if (val >= 10^exp & val <= 3*10^exp)
                             list(ceiling(val/10^exp)*10^(exp-1), TRUE)
                           else
                             list(10^exp, FALSE)
                         }, 
                         exp = lower_exp)
    intrvl_res <- dis_to_low[[1]]
    y_lower_lim <- min(data_count[[value_name]]) %/% intrvl_res * intrvl_res
    y_lower_lim <- if (dis_to_low[[2]]) y_lower_lim - intrvl_res else y_lower_lim
    breaks_to <- max(data[[value_name]]) * expand_coef_global
    breaks_by <- intrvl_res/2
    # ybreaks <- seq(y_lower_lim, max(data[[value_name]]), intrvl_res/2)
  }
  else if (max(data_count[[value_name]] + data_count$sd) <= 1){
    breaks_to <- 1
    breaks_by <- 0.2
  }
    # ybreaks <- seq(0, 1, 0.2)
  else{
    breaks_to <- max(data[[value_name]]) * expand_coef_global
    bar_upper_lim <- max(data_count[[value_name]] + data_count$sd)
    breaks_by <- sapply(bar_upper_lim, function(x){
      if (x <= 2) 0.2
      else if (x <= 20) 5
      else if (x <= 50) 10
      else if (x <= 100) 20
      else if (x <= 200) 40
      else 50
    })
  }
  # else if (max(data_count[[value_name]] + data_count$sd) <= 2)
  #   ybreaks <- seq(0, max(data[[value_name]]), 0.2)
  # else if (max(data_count[[value_name]] + data_count$sd) <= 20)
  #   ybreaks <- seq(0, max(data[[value_name]]), 5)
  # else if (max(data_count[[value_name]] + data_count$sd) <= 50)
  #   ybreaks <- seq(0, max(data[[value_name]]), 10)
  # else if (max(data_count[[value_name]] + data_count$sd) <= 100)
  #   ybreaks <- seq(0, max(data[[value_name]]), 20)
  # else
  #   ybreaks <- seq(0, max(data[[value_name]]), 50)
  y_lower_lim <- if (is.null(y_lower_lim)) 0 else y_lower_lim
  ybreaks <- seq(y_lower_lim, breaks_to, breaks_by)
  # Set y-axis attribute: upper limit, adjust the breaks
  rightclust <- filter(data_count, cluster == max(data_count$cluster))
  rightclust_upper_expand <- 
    (max(rightclust[[value_name]] + rightclust$sd) - y_lower_lim) * expand_coef_right
  global_upper_expand <- 
    (max(data_count[[value_name]] + data_count$sd) - y_lower_lim) * expand_coef_global
  y_upper_lim <- 
    max(rightclust_upper_expand, global_upper_expand) + y_lower_lim
  for (i in length(ybreaks):1){
    if ((y_upper_lim - ybreaks[i])/(y_upper_lim - y_lower_lim) < ytick_limit)
      ybreaks <- ybreaks[-i]
    else break
  }
  # minor_intrvl <- (ybreaks[2] - ybreaks[1])/5
  # y_minorbreaks <- c()
  # for (i in 1:(length(ybreaks)-1))
  #   y_minorbreaks <- append(y_minorbreaks, seq(from = ybreaks[i] + minor_intrvl, 
  #                                              by = minor_intrvl,
  #                                              length.out = 4))
  # Set y-axis (breaks, range, ticks), legend, clear the background grids and color
  p <- p +
    scale_y_continuous(breaks = ybreaks, expand = expansion(mult = c(0, 0)),
                       limits = c(y_lower_lim, y_upper_lim), na.value = y_lower_lim) +  # 让x轴与条柱贴合
    ylab(paste0(ylabel_norm, ylabel_pref, ylabel_suff)) +
    theme_bw() +
    theme(axis.line.x.bottom = 
            element_line("black", 
                         arrow = arrow(angle = arrow_angle, length = unit(10, "bigpts"), 
                                       ends = "last", type = "closed")),
          axis.line.y.left = 
            element_line("black", 
                         arrow = arrow(angle = arrow_angle, length = unit(10, "bigpts"), 
                                       ends = "last", type = "closed")),
          axis.text.x = element_text(size = 17, color = "black"),
          axis.text.y = element_text(size = 17, color = "black"),
          axis.title.x = element_text(face = "bold", size = 19),
          axis.title.y = element_text(face = "bold", size = 19),
          legend.background = element_rect(colour = "black"),
          # legend.box.spacing = unit(3, "bigpts"),
          legend.margin = margin(2, -13, 7, 7),
          # legend.key = element_rect(fill = "white", colour = "black", size = 0.2/72*25.4),
          legend.position = c(0.85, 0.90),
          legend.text = element_text(size = 16),
          legend.title = element_blank(),
          panel.grid.major = element_blank(),
          panel.grid.minor = element_blank(),
          panel.background = element_rect(fill = "transparent"),
          panel.border = element_blank(),
          plot.background = element_rect(fill = "transparent")
          )
  
  # Print and save the plot with the assigned directory and file name
  show(p)
  save_dir <- paste(SAVE_ROOT, paste(type, 'plot', sep = '_'), sep = '/')
  if (!low_res == 1) save_dir <- paste0(save_dir, '_', as.character(low_res), 'res')
  if (!dir.exists(save_dir)) dir.create(save_dir)
  file_path <- paste(save_dir, paste(file_name, file_type, sep = '.'), sep = '/')
  if (file.exists(file_path)) file.remove(file_path)
  # switch(file_type,
  #        "bmp" = bmp(file_path, width = 1280, height = 1280, res = 144),
  #        "jpeg" = jpeg(file_path, width = 1280, height = 1280, res = 144),
  #        "jpg" = jpeg(file_path, width = 1280, height = 1280, res = 144),
  #        "png" = png(file_path, width = 1280, height = 1280, res = 144),
  #        "tif" = tiff(file_path, width = 1280, height = 1280, res = 144),
  #        "tiff" = tiff(file_path, width = 1280, height = 1280, res = 144))
  dev.print(png, file_path, width = plot_width*low_res, height = plot_height*low_res, res = 600*low_res)
  dev.off()
  return(p)
}

if (FALSE){
  LOW_RES = 0.5
  ### 大环赛的图片
  ## 平均单赛段排名
  grand_sc_avg_ranks_melt <-
    get_melt_info(grand_sc_fltrd, criterion = "avg", var = "ranks",
                  ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化排名
  # grand_sc_norm_avg_ranks_melt <-
  #   get_melt_info(grand_sc_normalize_kmeans$data$ranks, criterion = "avg", var = "ranks",
  #                 ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_norm_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_kmeans_norm_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段排名
  grand_sc_best_ranks_melt <-
    get_melt_info(grand_sc_fltrd, criterion = "best", var = "ranks",
                  ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_best_ranks_melt$data, value_type = "ranks",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)

  ## 平均单赛段均速
  grand_sc_avg_speed2median_melt <-
    get_melt_info(grand_sc_fltrd, criterion = "avg", var = "speed2median",
                  ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化均速
  grand_sc_norm_avg_speed2median_melt <-
    get_melt_info(grand_sc_normalize_kmeans$data$speed2median, criterion = "avg", var = "speed2median",
                  ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_norm_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_kmeans_norm_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段均速
  grand_sc_best_speed2median_melt <-
    get_melt_info(grand_sc_fltrd, criterion = "best", var = "speed2median",
                  ref = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_best_speed2median_melt$data, value_type = "speed2median",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
  
  ## 平均GC排名
  grand_gc_avg_ranks_melt <-
    get_melt_info(grand_gc_fltrd, criterion = "avg", var = "ranks",
                  races_filter = "grand_tour")
  p <- auto_plot(grand_gc_avg_ranks_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "ranks", criterion = "avg", type = "bar",
                 file_name = "grand_gc_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳GC排名
  grand_gc_best_ranks_melt <-
    get_melt_info(grand_gc_fltrd, criterion = "best", var = "ranks",
                  races_filter = "grand_tour")
  p <- auto_plot(grand_gc_best_ranks_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "ranks", criterion = "best", type = "bar",
                 file_name = "grand_gc_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均全程均速
  grand_gc_avg_speed2median_melt <-
    get_melt_info(grand_gc_fltrd, criterion = "avg", var = "speed2median",
                  races_filter = "grand_tour")
  p <- auto_plot(grand_gc_avg_speed2median_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "speed2median", criterion = "avg", type = "bar",
                 file_name = "grand_gc_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳全程均速
  grand_gc_best_speed2median_melt <-
    get_melt_info(grand_gc_fltrd, criterion = "best", var = "speed2median",
                  races_filter = "grand_tour")
  p <- auto_plot(grand_gc_best_speed2median_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "speed2median", criterion = "best", type = "bar",
                 file_name = "grand_gc_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
  
  ### 其他多日赛的图片
  ## 平均单赛段排名
  other_multi_sc_avg_ranks_melt <-
    get_melt_info(other_multi_sc_fltrd_matched, criterion = "avg", var = "ranks")
  p <- auto_plot(other_multi_sc_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", type = "bar",
                 file_name = "other_multi_sc_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段排名
  other_multi_sc_best_ranks_melt <-
    get_melt_info(other_multi_sc_fltrd_matched, criterion = "best", var = "ranks")
  p <- auto_plot(other_multi_sc_best_ranks_melt$data, value_type = "ranks",
                 criterion = "best", type = "bar",
                 file_name = "other_multi_sc_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段均速
  other_multi_sc_avg_speed2median_melt <-
    get_melt_info(other_multi_sc_fltrd_matched, criterion = "avg", var = "speed2median")
  p <- auto_plot(other_multi_sc_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", type = "bar",
                 file_name = "other_multi_sc_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段均速
  other_multi_sc_best_speed2median_melt <-
    get_melt_info(other_multi_sc_fltrd_matched, criterion = "best", var = "speed2median")
  p <- auto_plot(other_multi_sc_best_speed2median_melt$data, value_type = "speed2median",
                 criterion = "best", type = "bar",
                 file_name = "other_multi_sc_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)

  ## 平均GC排名
  other_multi_gc_avg_ranks_melt <-
    get_melt_info(other_multi_gc_fltrd_matched, criterion = "avg", var = "ranks",
                  races_filter = "other_multi")
  p <- auto_plot(other_multi_gc_avg_ranks_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "ranks", criterion = "avg", type = "bar",
                 file_name = "other_multi_gc_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳GC排名
  other_multi_gc_best_ranks_melt <-
    get_melt_info(other_multi_gc_fltrd_matched, criterion = "best", var = "ranks",
                  races_filter = "other_multi")
  p <- auto_plot(other_multi_gc_best_ranks_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "ranks", criterion = "best", type = "bar",
                 file_name = "other_multi_gc_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均全程均速
  other_multi_gc_avg_speed2median_melt <-
    get_melt_info(other_multi_gc_fltrd_matched, criterion = "avg", var = "speed2median",
                  races_filter = "other_multi")
  p <- auto_plot(other_multi_gc_avg_speed2median_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "speed2median", criterion = "avg", type = "bar",
                 file_name = "other_multi_gc_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳全程均速
  other_multi_gc_best_speed2median_melt <-
    get_melt_info(other_multi_gc_fltrd_matched, criterion = "best", var = "speed2median",
                  races_filter = "other_multi")
  p <- auto_plot(other_multi_gc_best_speed2median_melt$data, var_name = "races", is_gc = TRUE,
                 value_type = "speed2median", criterion = "best", type = "bar",
                 file_name = "other_multi_gc_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
  
  ### 大环赛GC排名前10%车手的图片
  ## 平均单赛段排名
  grand_sc_top10percent_avg_ranks_melt <-
    get_melt_info(grand_sc_top10percent_gc, criterion = "avg", var = "ranks")
  p <- auto_plot(grand_sc_top10percent_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化排名
  grand_sc_top10percent_norm_avg_ranks_melt <-
    get_melt_info(grand_sc_top10percent_normalize_kmeans$data$ranks, criterion = "avg", var = "ranks",
                  ref = grand_sc_top10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_top10percent_norm_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_norm_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段排名
  grand_sc_top10percent_best_ranks_melt <-
    get_melt_info(grand_sc_top10percent_gc, criterion = "best", var = "ranks")
  p <- auto_plot(grand_sc_top10percent_best_ranks_melt$data, value_type = "ranks",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)

  ## 平均单赛段均速
  grand_sc_top10percent_avg_speed2median_melt <-
    get_melt_info(grand_sc_top10percent_gc, criterion = "avg", var = "speed2median")
  p <- auto_plot(grand_sc_top10percent_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化均速
  grand_sc_top10percent_norm_avg_speed2median_melt <-
    get_melt_info(grand_sc_top10percent_normalize_kmeans$data$speed2median, criterion = "avg", var = "speed2median",
                  ref = grand_sc_top10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_top10percent_norm_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_norm_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段均速
  grand_sc_top10percent_best_speed2median_melt <-
    get_melt_info(grand_sc_top10percent_gc, criterion = "best", var = "speed2median")
  p <- auto_plot(grand_sc_top10percent_best_speed2median_melt$data, value_type = "speed2median",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_top10percent_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
  
  ### 大环赛GC排名中间10%车手的图片
  ## 平均单赛段排名
  grand_sc_mid10percent_avg_ranks_melt <-
    get_melt_info(grand_sc_mid10percent_gc, criterion = "avg", var = "ranks")
  p <- auto_plot(grand_sc_mid10percent_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化排名
  grand_sc_mid10percent_norm_avg_ranks_melt <-
    get_melt_info(grand_sc_mid10percent_normalize_kmeans$data$ranks, criterion = "avg", var = "ranks",
                  ref = grand_sc_mid10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_mid10percent_norm_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_norm_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段排名
  grand_sc_mid10percent_best_ranks_melt <-
    get_melt_info(grand_sc_mid10percent_gc, criterion = "best", var = "ranks")
  p <- auto_plot(grand_sc_mid10percent_best_ranks_melt$data, value_type = "ranks",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)

  ## 平均单赛段均速
  grand_sc_mid10percent_avg_speed2median_melt <-
    get_melt_info(grand_sc_mid10percent_gc, criterion = "avg", var = "speed2median")
  p <- auto_plot(grand_sc_mid10percent_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化均速
  grand_sc_mid10percent_norm_avg_speed2median_melt <-
    get_melt_info(grand_sc_mid10percent_normalize_kmeans$data$speed2median, criterion = "avg", var = "speed2median",
                  ref = grand_sc_mid10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_mid10percent_norm_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_norm_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段均速
  grand_sc_mid10percent_best_speed2median_melt <-
    get_melt_info(grand_sc_mid10percent_gc, criterion = "best", var = "speed2median")
  p <- auto_plot(grand_sc_mid10percent_best_speed2median_melt$data, value_type = "speed2median",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_mid10percent_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
  
  ### 大环赛GC排名后10%车手的图片
  ## 平均单赛段排名
  grand_sc_bottom10percent_avg_ranks_melt <-
    get_melt_info(grand_sc_bottom10percent_gc, criterion = "avg", var = "ranks")
  p <- auto_plot(grand_sc_bottom10percent_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化排名
  grand_sc_bottom10percent_norm_avg_ranks_melt <-
    get_melt_info(grand_sc_bottom10percent_normalize_kmeans$data$ranks, criterion = "avg", var = "ranks",
                  ref = grand_sc_bottom10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_bottom10percent_norm_avg_ranks_melt$data, value_type = "ranks",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_norm_avg_ranks", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段排名
  grand_sc_bottom10percent_best_ranks_melt <-
    get_melt_info(grand_sc_bottom10percent_gc, criterion = "best", var = "ranks")
  p <- auto_plot(grand_sc_bottom10percent_best_ranks_melt$data, value_type = "ranks",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_best_ranks", file_type = "png", low_res = LOW_RES)

  ## 平均单赛段均速
  grand_sc_bottom10percent_avg_speed2median_melt <-
    get_melt_info(grand_sc_bottom10percent_gc, criterion = "avg", var = "speed2median")
  p <- auto_plot(grand_sc_bottom10percent_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 平均单赛段标准化均速
  grand_sc_bottom10percent_norm_avg_speed2median_melt <-
    get_melt_info(grand_sc_bottom10percent_normalize_kmeans$data$speed2median, criterion = "avg", var = "speed2median",
                  ref = grand_sc_bottom10percent_normalize_kmeans$`k-means model`$ranks$cluster)
  p <- auto_plot(grand_sc_bottom10percent_norm_avg_speed2median_melt$data, value_type = "speed2median",
                 criterion = "avg", normalized = TRUE, type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_norm_avg_speed2median", file_type = "png", low_res = LOW_RES)
  ## 最佳单赛段均速
  grand_sc_bottom10percent_best_speed2median_melt <-
    get_melt_info(grand_sc_bottom10percent_gc, criterion = "best", var = "speed2median")
  p <- auto_plot(grand_sc_bottom10percent_best_speed2median_melt$data, value_type = "speed2median",
                 criterion = "best", type = "bar",
                 file_name = "grand_sc_bottom10percent_kmeans_best_speed2median", file_type = "png", low_res = LOW_RES)
}

