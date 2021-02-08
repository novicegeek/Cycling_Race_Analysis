library(cluster)  # for cluster::silhouette()
library(factoextra)
source('basics.R')


HOPKINS_THRESHOLD = 0.5


kmeans_sc <- function(input, hopkins=FALSE){
  set.seed(123)
  ranks <- input[, append('ID', cols_paste('Avg Rank'))]
  speed2median <- input[, append('ID', cols_paste('Avg Avg Speed Rel to Median'))]
  
  # 1. Calculate Hopkins Statistic
  if (hopkins){
    ranks_hpkins <- get_clust_tendency(data = ranks[, 2:4],
                                       n = round(nrow(ranks)/10),
                                       graph = FALSE)$hopkins_stat
    median_hpkins <- get_clust_tendency(data = speed2median[, 2:4],
                                        n = round(nrow(speed2median)/10),
                                        graph = FALSE)$hopkins_stat
    if (ranks_hpkins < HOPKINS_THRESHOLD){
      print("No deviance from randomness for average rank data")
      return()
    }else if (median_hpkins < HOPKINS_THRESHOLD){
      print("No deviance from randomness for average speed relative to median data")
      return()
    }
  }
  
  
  # 2. Calculate the optimal number of clusters
  # 2.0 Calculate the dissimilarity object
  ranks_dist <- dist(ranks[, 2:4], method = "euclid", diag = FALSE, upper = FALSE)
  median_dist <- dist(speed2median[, 2:4], method = "euclid", diag = FALSE, upper = FALSE)
  # 2.1 WSS (Elbow) method
  show(fviz_nbclust(x = ranks[, 2:4], FUNcluster = kmeans, method = "wss",
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Rank"))
  show(fviz_nbclust(x = speed2median[, 2:4], FUNcluster = kmeans, method = "wss",
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Average Speed Relative to Median"))
  # 2.2 Silhouette coefficient
  show(fviz_nbclust(x = ranks[, 2:4], FUNcluster = kmeans, method = "silhouette", diss = ranks_dist,
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Rank"))
  show(fviz_nbclust(x = speed2median[, 2:4], FUNcluster = kmeans, method = "silhouette", diss = median_dist,
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Average Speed Relative to Median"))
  # 2.3 Gap statistic
  show(fviz_nbclust(x = ranks[, 2:4], FUNcluster = kmeans, method = "gap_stat",
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Rank"))
  show(fviz_nbclust(x = speed2median[, 2:4], FUNcluster = kmeans, method = "gap_stat",
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Average Speed Relative to Median"))
  
  confirm <- "n"
  while (confirm == "n"){
    ranks_optimal_k <- as.integer(readline(
      "Determine the optimal number of clusters for clustering by rank: "
      ))
    median_optimal_k <- as.integer(readline(
      "Determine the optimal number of clusters for clustering by median: "
      ))
    while (confirm != "y" ){
      sprintf("You set the optimal number for rank/median to: %d/%d, respectively. 
              Confirm it by pressing 'y', or press 'n' to re-set: ", ranks_optimal_k, median_optimal_k)
      confirm <- readline()
    }
  }
  
  # 3. Do clustering according to the optimal number of clusters
  ranks_kmeans <- kmeans(ranks[, 2:4], centers = ranks_optimal_k, nstart = 10)
  median_kmeans <- kmeans(speed2median[, 2:4], centers = median_optimal_k, nstart = 10)
  
  # 4. Examine the clustering results
  # 4.1 Visual inspection
  show(fviz_cluster(ranks_kmeans, ranks[, 2:4], geom = "point", 
                    repel = TRUE, stand = FALSE, show.clust.cent = TRUE, 
                    ellipse.type = "convex", main = "Clustering by Average Rank"))
  show(fviz_cluster(median_kmeans, speed2median[, 2:4], geom = "point", 
                    repel = TRUE, stand = FALSE, show.clust.cent = TRUE, 
                    ellipse.type = "convex", main = "Clustering by Average Average Speed Relative to Median"))
  # 4.2 Silhouette coefficient
  ranks_sil <- silhouette(ranks_kmeans$cluster, dist = ranks_dist)
  median_sil <- silhouette(median_kmeans$cluster, dist = median_dist)
  
  # 5. Add the cluster assignments and silhouettes to the dataframe
  ranks <- cbind(ranks, list('cluster' = ranks_kmeans$cluster,
                             'neighbor' = ranks_sil[, "neighbor"],
                             'silhouette' = ranks_sil[, "sil_width"]))
  speed2median <- cbind(speed2median, list('cluster' = median_kmeans$cluster,
                                           'neighbor' = median_sil[, "neighbor"],
                                           'silhouette' = median_sil[, "sil_width"]))
  
  # 6. Return important results
  list('data' = list('ranks' = ranks, 'speed2median' = speed2median), 
       'Hopkins statistic' = list('ranks' = ranks_hpkins, 'speed2median' = median_hpkins),
       'optimal k' = list('ranks' = ranks_optimal_k, 'speed2median' = median_optimal_k),
       'k-means model' = list('ranks' = ranks_kmeans, 'speed2median' = median_kmeans),
       'silhouette' = list('ranks' = ranks_sil, 'speed2median' = median_sil))
}