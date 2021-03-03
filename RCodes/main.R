source('basics.R')
source('kmeans.R')
require(NbClust)

# grand_sc_kmeans <- kmeans_sc(grand_sc_fltrd,
#                              method = "euclidean",
#                              stage_class = "profile",
#                              hopkins = TRUE,
#                              normalize = FALSE)
# grand_sc_normalize_kmeans <- kmeans_sc(grand_sc_fltrd,
#                                        method = "euclidean",
#                                        stage_class = "profile",
#                                        hopkins = TRUE,
#                                        normalize = TRUE)
# grand_sc_normalize_kmeans_2clust <- kmeans_sc(grand_sc_fltrd,
#                                               method = "euclidean",
#                                               stage_class = "profile",
#                                               hopkins = FALSE,
#                                               normalize = TRUE)
# grand_sc_skmeans_3clust <- kmeans_sc(grand_sc_fltrd,
#                                      method = "spherical",
#                                      stage_class = "profile",
#                                      hopkins = FALSE,
#                                      normalize = FALSE)
# grand_sc_speedquantile0.25_kmeans <- kmeans_sc(grand_sc_by_speedquantile0.25_fltrd,
#                                                method = "euclidean",
#                                                stage_class = "speed quantile",
#                                                hopkins = TRUE,
#                                                normalize = FALSE)

# grand_sc_kmeans <- add_aggr(grand_sc_kmeans, 
#                             grand_sc_normalize_kmeans, 
#                             cluster_by = "ranks", mean)
# grand_sc_normalize_kmeans <- add_aggr(grand_sc_normalize_kmeans,
#                                       grand_sc_normalize_kmeans,
#                                       cluster_by = "ranks", mean)
# grand_sc_skmeans <- add_aggr(grand_sc_skmeans, grand_sc_skmeans,
#                              cluster_by = "ranks", mean)
# grand_sc_skmeans_3clust <- add_aggr(grand_sc_skmeans_3clust, 
#                                     grand_sc_skmeans_3clust,
#                                     cluster_by = "ranks", mean)

all_gc_by_profile <- read_csv(
  "F:/Documents/Li/Master'sThesis/Data/Cyclist_Meta/GC/cyclist_meta_merged_all_GC.csv")
grand_gc_fltrd <- filter_data(all_gc_by_profile,
                              races_filter = 'grand_tour',
                              result_type = 'GC',
                              stage_class = 'profile',
                              limit = 3)


if (FALSE){
  ## Test of cluster attributes on GC data of other multi-stage races 
  # Match the cyclists in filtered SC data to filtered GC data
  # And write the cluster assignments by normalized-ranks clustering
  tmatch_tmp <- match(grand_sc_fltrd$ID, grand_gc_fltrd$ID, nomatch = FALSE)
  for (i in 1:length(tmatch_tmp))
    if (tmatch_tmp[i] > 0)
      grand_gc_fltrd[tmatch_tmp[i], 'cluster'] <- 
        grand_sc_normalize_kmeans$data$ranks$cluster[i]
  # Match the cyclists in filtered Grand-Tour GC data to filtered other 
  # multi-stage races GC data, and write the cluster assignments
  tmatch <- match(grand_gc_fltrd$ID, other_multi_gc_fltrd$ID, nomatch = FALSE)
  for (i in 1:length(tmatch))
    if (tmatch[i] > 0)
      other_multi_gc_fltrd[tmatch[i], 'cluster'] <- grand_gc_fltrd$cluster[i]
  # Filter the matched cyclists in filtered other multi-stage races GC data
  # And calculate the aggregate information
  other_multi_gc_fltrd_matched <- dplyr::filter(other_multi_gc_fltrd, !is.na(cluster))
  other_multi_gc_fltrd_matched_aggregate <- 
    get_cluster_gc_info(other_multi_gc_fltrd_matched,
                        other_multi_gc_fltrd_matched,
                        races_filter = "other_multi",
                        cluster_by = "ranks",
                        method = "kmeans")
  
  ## Test of cluster attributes on SC data of other multi-stage races
  # Match the cyclists in filtered Grand-Tour SC data to filtered other 
  # multi-stage races SC data, and attach the cluster assignments
  tmatch_tmp <- match(grand_sc_fltrd$ID, other_multi_sc_fltrd$ID, nomatch = FALSE)
  for (i in 1:length(tmatch_tmp))
    if (tmatch_tmp[i] > 0)
      other_multi_sc_fltrd[tmatch_tmp[i], 'cluster'] <- 
        grand_sc_normalize_kmeans$data$ranks$cluster[i]
  # Filter the matched cyclists in filtered other multi-stage races SC data
  # And calculate the aggregate information
  other_multi_sc_fltrd_matched <- dplyr::filter(other_multi_sc_fltrd, !is.na(cluster))
  other_multi_sc_fltrd_matched_aggregate <- list(
    'data' = list(
      'ranks' = as.data.frame(other_multi_sc_fltrd_matched[c('ID', 
                                                             'Plain: Avg Rank', 
                                                             'Medium: Avg Rank', 
                                                             'High: Avg Rank')]),
      'speed2median' = as.data.frame(other_multi_sc_fltrd_matched[, c('ID', 
                                                                      'Plain: Avg Avg Speed Rel to Median', 
                                                                      'Medium: Avg Avg Speed Rel to Median', 
                                                                      'High: Avg Avg Speed Rel to Median')])
      )
    )
  other_multi_sc_fltrd_matched_aggregate <- 
    add_aggr(other_multi_sc_fltrd_matched_aggregate, other_multi_sc_fltrd_matched$cluster,
             cluster_by = "ranks", func = mean)
  # Write the numbers of cyclists in each cluster into the aggregate object
  tv <- aggregate(other_multi_sc_fltrd_matched$ID, 
                  by = list(other_multi_sc_fltrd_matched$cluster),
                  FUN = length)[ ,2]
  other_multi_sc_fltrd_matched_aggregate$`aggregate by norm cluster`$
    ranks[, 5] <- list('n' = tv)
  other_multi_sc_fltrd_matched_aggregate$`aggregate by norm cluster`$
    speed2median[, 5] <- list('n' = tv)
  other_multi_sc_fltrd_matched_aggregate$`aggregate order by norm cluster`$
    ranks[, 5] <- list('n' = tv)
  other_multi_sc_fltrd_matched_aggregate$`aggregate order by norm cluster`$
    speed2median[, 5] <- list('n' = tv)
  other_multi_sc_fltrd_matched_aggregate$data$ranks$cluster <- 
    other_multi_sc_fltrd_matched$cluster

  ## Analyze on cyclists in different quantiles of average Grand-Tour GC ranks
  # Calculate the boundaries for the top, middle and bottom 10% intervals
  # And splice the cyclists
  quantiles_grand_gc_rank <- 
    quantile(grand_gc_fltrd$`Grand Tour: Avg Rank`,
             probs = c(0.1, 0.45, 0.55, 0.9),
             names = TRUE)
  grand_gc_fltrd_top10percent <- 
    filter(grand_gc_fltrd, 
           `Grand Tour: Avg Rank` <= tertiles_grand_gc_rank['10%'])
  grand_gc_fltrd_mid10percent <- 
    filter(grand_gc_fltrd, 
           `Grand Tour: Avg Rank` > tertiles_grand_gc_rank['45%'] & 
             `Grand Tour: Avg Rank` <= tertiles_grand_gc_rank['55%'])
  grand_gc_fltrd_bottom10percent <- 
    filter(grand_gc_fltrd, 
           `Grand Tour: Avg Rank` > tertiles_grand_gc_rank['90%'])
  # Match the cyclists at different levels to their rows in the filtered 
  # Grand-Tour SC data, and splice out their SC data, respectively
  tmatch_top10percent <- match(grand_gc_fltrd_top10percent$ID, 
                               grand_sc_fltrd$ID, nomatch = FALSE)
  tmatch_mid10percent <- match(grand_gc_fltrd_mid10percent$ID, 
                               grand_sc_fltrd$ID, nomatch = FALSE)
  tmatch_bottom10percent <- match(grand_gc_fltrd_bottom10percent$ID, 
                                  grand_sc_fltrd$ID, nomatch = FALSE)
  grand_sc_top10percent_gc <- grand_sc_fltrd[tmatch_top10percent, ]
  grand_sc_mid10percent_gc <- grand_sc_fltrd[tmatch_mid10percent, ]
  grand_sc_bottom10percent_gc <- grand_sc_fltrd[tmatch_bottom10percent, ]
  # Normalize the SC data
  grand_sc_top10percent_gc_normalize <- 
    kmeans_sc(grand_sc_top10percent_gc, "euclidean", "profile", 
              hopkins = FALSE, normalize = TRUE)$data
  grand_sc_mid10percent_gc_normalize <- 
    kmeans_sc(grand_sc_mid10percent_gc, "euclidean", "profile", 
              hopkins = FALSE, normalize = TRUE)$data
  grand_sc_bottom10percent_gc_normalize <- 
    kmeans_sc(grand_sc_bottom10percent_gc, "euclidean", "profile", 
              hopkins = FALSE, normalize = TRUE)$data
  # Calculate the Hopkins statistic (turns out all are close to or over .8)
  get_clust_tendency(grand_sc_top10percent_gc_normalize$ranks[, 2:4], 50)
  get_clust_tendency(grand_sc_top10percent_gc_normalize$speed2median[, 2:4], 50)
  get_clust_tendency(grand_sc_mid10percent_gc_normalize$ranks[, 2:4], 50)
  get_clust_tendency(grand_sc_mid10percent_gc_normalize$speed2median[, 2:4], 50)
  get_clust_tendency(grand_sc_bottom10percent_gc_normalize$ranks[, 2:4], 50)
  get_clust_tendency(grand_sc_bottom10percent_gc_normalize$speed2median[, 2:4], 50)
  # Calculate the optimal numbers of clusters when clustering with K-means on normalized ranks
  # Optimal-k: 2, 3, 2 for top, middle and bottom cyclists, respectively
  nbclust_grand_sc_top10_norm_ranks_kmeans <- NbClust(
    grand_sc_top10percent_gc_normalize$ranks[, 2:4], method = "kmeans")
  nbclust_grand_sc_mid10_norm_ranks_kmeans <- NbClust(
    grand_sc_mid10percent_gc_normalize$ranks[, 2:4], method = "kmeans")
  nbclust_grand_sc_bottom10_norm_ranks_kmeans <- NbClust(
    grand_sc_bottom10percent_gc_normalize$ranks[, 2:4], method = "kmeans")
  # Do normalized K-means
  # And set the number of clusters of ranks-clustering to 2, 3, 2, respectively
  grand_sc_top10percent_normalize_kmeans <- 
    kmeans_sc(grand_sc_top10percent_gc, "euclidean", "profile", normalize = TRUE)
  grand_sc_mid10percent_normalize_kmeans <- 
    kmeans_sc(grand_sc_mid10percent_gc, "euclidean", "profile", normalize = TRUE)
  grand_sc_bottom10percent_normalize_kmeans <- 
    kmeans_sc(grand_sc_bottom10percent_gc, "euclidean", "profile", normalize = TRUE)
  # Calculate the aggregate information
  grand_sc_top10percent_normalize_kmeans <- 
    add_aggr(grand_sc_top10percent_normalize_kmeans, 
             grand_sc_top10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  grand_sc_mid10percent_normalize_kmeans <- 
    add_aggr(grand_sc_mid10percent_normalize_kmeans, 
             grand_sc_mid10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  grand_sc_bottom10percent_normalize_kmeans <- 
    add_aggr(grand_sc_bottom10percent_normalize_kmeans, 
             grand_sc_bottom10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  grand_sc_top10percent_gc_aggregate <- list(
    'data' = list(
      'ranks' = as.data.frame(grand_sc_top10percent_gc[, c('ID',
                                                           'Plain: Avg Rank',
                                                           'Medium: Avg Rank',
                                                           'High: Avg Rank')]),
      'speed2median' = as.data.frame(grand_sc_top10percent_gc[, c('ID',
                                                                  'Plain: Avg Avg Speed Rel to Median',
                                                                  'Medium: Avg Avg Speed Rel to Median',
                                                                  'High: Avg Avg Speed Rel to Median')])
    )
  )
  grand_sc_top10percent_gc_aggregate <- 
    add_aggr(grand_sc_top10percent_gc_aggregate,
             grand_sc_top10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  grand_sc_mid10percent_gc_aggregate <- list(
    'data' = list(
      'ranks' = as.data.frame(grand_sc_mid10percent_gc[, c('ID',
                                                           'Plain: Avg Rank',
                                                           'Medium: Avg Rank',
                                                           'High: Avg Rank')]),
      'speed2median' = as.data.frame(grand_sc_mid10percent_gc[, c('ID',
                                                                  'Plain: Avg Avg Speed Rel to Median',
                                                                  'Medium: Avg Avg Speed Rel to Median',
                                                                  'High: Avg Avg Speed Rel to Median')])
    )
  )
  grand_sc_mid10percent_gc_aggregate <- 
    add_aggr(grand_sc_mid10percent_gc_aggregate,
             grand_sc_mid10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  grand_sc_bottom10percent_gc_aggregate <- list(
    'data' = list(
      'ranks' = as.data.frame(grand_sc_bottom10percent_gc[, c('ID',
                                                              'Plain: Avg Rank',
                                                              'Medium: Avg Rank',
                                                              'High: Avg Rank')]),
      'speed2median' = as.data.frame(grand_sc_bottom10percent_gc[, c('ID',
                                                                     'Plain: Avg Avg Speed Rel to Median',
                                                                     'Medium: Avg Avg Speed Rel to Median',
                                                                     'High: Avg Avg Speed Rel to Median')])
    )
  )
  grand_sc_bottom10percent_gc_aggregate <- 
    add_aggr(grand_sc_bottom10percent_gc_aggregate,
             grand_sc_bottom10percent_normalize_kmeans,
             cluster_by = "ranks", mean)
  # Add the clusters assignments
  grand_sc_top10percent_gc$cluster <- 
    grand_sc_top10percent_normalize_kmeans$data$ranks$cluster
  grand_sc_mid10percent_gc$cluster <- 
    grand_sc_mid10percent_normalize_kmeans$data$ranks$cluster
  grand_sc_bottom10percent_gc$cluster <- 
    grand_sc_bottom10percent_normalize_kmeans$data$ranks$cluster
  
  # Filter those in other_multi data from grand data
  grand_other_multi_match <- list()
  grand_other_multi_match$grand_sc_matched <- 
    dplyr::filter(grand_sc_fltrd, ID %in% other_multi_sc_fltrd_matched$ID)
  grand_other_multi_match$other_multi_sc_matched <- other_multi_sc_fltrd_matched
  grand_other_multi_match$grand_gc_matched <- 
    dplyr::filter(grand_gc_fltrd, ID %in% other_multi_gc_fltrd_matched$ID)
  grand_other_multi_match$other_multi_gc_matched <- other_multi_gc_fltrd_matched
  for (i in 1:nrow(grand_other_multi_match$grand_sc_matched)){
    match_row <- pmatch(grand_other_multi_match$grand_sc_matched$ID[i], 
                        grand_other_multi_match$other_multi_sc_matched$ID)
    grand_other_multi_match$grand_sc_matched[i, 'cluster'] <- 
      grand_other_multi_match$other_multi_sc_matched$cluster[match_row]
  }
  # Get the difference between other_multi and grand for the same group of cyclists 
  grand_other_multi_match$sc_other_multi_minus_grand <- grand_other_multi_match$other_multi_sc_matched[, 1:3]
  grand_other_multi_match$gc_other_multi_minus_grand <- grand_other_multi_match$other_multi_gc_matched[, 1:3]
  for (criterion in c("Avg", "Best"))
    for (field in c("Rank", "Avg Speed Rel to Median")){
      for (profile in PROFILES){
        col_name <- paste(profile, paste(criterion, field), sep = ": ")
        grand_other_multi_match$sc_other_multi_minus_grand[col_name] <- 
          grand_other_multi_match$other_multi_sc_matched[col_name] - 
          grand_other_multi_match$grand_sc_matched[col_name]
      }
      col_name <- paste(criterion, field)
      grand_col_name <- paste("Grand Tour", paste(criterion, field), sep = ": ")
      other_col_name <- paste("Other Multi", paste(criterion, field), sep = ": ")
      grand_other_multi_match$gc_other_multi_minus_grand[col_name] <- 
        grand_other_multi_match$other_multi_gc_matched[other_col_name] - 
        grand_other_multi_match$grand_gc_matched[grand_col_name]
    }
  grand_other_multi_match$sc_other_multi_minus_grand$cluster <- 
    grand_other_multi_match$other_multi_sc_matched$cluster
  grand_other_multi_match$gc_other_multi_minus_grand$cluster <- 
    grand_other_multi_match$other_multi_gc_matched$cluster
  # Get summary of the difference
  diff_summary <- list('sc' = list(), 'gc' = list())
  for (col_name in colnames(grand_other_multi_match$sc_other_multi_minus_grand)[4:15])
    diff_summary$sc[[col_name]] <- 
    summarySE(grand_other_multi_match$sc_other_multi_minus_grand[, c(4:16)], 
              measurevar = col_name,
              groupvars = "cluster")
  for (col_name in colnames(grand_other_multi_match$gc_other_multi_minus_grand[4:7]))
    diff_summary$gc[[col_name]] <- 
    summarySE(grand_other_multi_match$gc_other_multi_minus_grand[, c(4:8)], 
              measurevar = col_name,
              groupvars = "cluster")
    
  
  # Get the rank quantiles (rank_norm) for grand and other_multi data
  rank_norm_summary <- list('grand' = list('sc' = list(), 'gc' = list()), 
                            'other_multi' = list('sc' = list(), 'gc' = list()))
  # Do for the grand
  for (criterion in c("Avg", "Best")){
    for (profile in PROFILES){
      col_name <- paste(profile, paste(criterion, "Rank_Norm"), sep = ": ")
      rank_norm_summary$grand$sc[[col_name]] <- 
        summarySE(cbind(grand_sc_fltrd, 
                        list('cluster' = grand_sc_normalize_kmeans$`k-means model`$ranks$cluster)), 
                  measurevar = col_name, groupvars = "cluster")
    }
    col_name <- paste("Grand Tour", paste(criterion, "Rank_Norm"), sep = ": ")
    rank_norm_summary$grand$gc[[col_name]] <- 
      summarySE(grand_gc_fltrd, measurevar = col_name, groupvars = "cluster")
  }
  # Do for the other_multi
  for (criterion in c("Avg", "Best")){
    for (profile in PROFILES){
      col_name <- paste(profile, paste(criterion, "Rank_Norm"), sep = ": ")
      rank_norm_summary$other_multi$sc[[col_name]] <- 
        summarySE(other_multi_sc_fltrd_matched, measurevar = col_name, groupvars = "cluster")
    }
    col_name <- paste("Other Multi", paste(criterion, "Rank_Norm"), sep = ": ")
    rank_norm_summary$other_multi$gc[[col_name]] <- 
      summarySE(other_multi_gc_fltrd_matched, measurevar = col_name, groupvars = "cluster")
  }
}


ggplot(mapping = aes(x = grand_sc_normalize_kmeans$data$ranks$cluster,
                     y = grand_gc_fltrd$`Grand Tour: Avg Rank`)) +
  geom_point()
ggplot(mapping = aes(group = grand_sc_normalize_kmeans$data$ranks$cluster,
                     y = grand_gc_fltrd$`Grand Tour: Avg Rank`)) +
  geom_boxplot()

save.image()
