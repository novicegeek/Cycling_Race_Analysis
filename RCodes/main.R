source('basics.R')
source('kmeans.R')

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
grand_gc_fltrd <- dplyr::filter(filter_data(all_gc_by_profile,
                                            races_filter = 'grand_tour',
                                            result_type = 'GC',
                                            stage_class = 'profile',
                                            limit = 3), ID %in% grand_sc_fltrd$ID)

ggplot(mapping = aes(x = grand_sc_normalize_kmeans$data$ranks$cluster,
                     y = grand_gc_fltrd$`Grand Tour: Avg Rank`)) +
  geom_point()
ggplot(mapping = aes(group = grand_sc_normalize_kmeans$data$ranks$cluster,
                     y = grand_gc_fltrd$`Grand Tour: Avg Rank`)) +
  geom_boxplot()

save.image()
