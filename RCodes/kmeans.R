require(cluster)  # for cluster::silhouette()
require(factoextra)
require(skmeans)
source('basics.R')


HOPKINS_THRESHOLD = 0.5


kmeans_sc <- function(input, 
                      method = c("euclidean", "spherical"),
                      stage_class = 'profile',
                      hopkins=TRUE, normalize=FALSE, 
                      maxiter = 20, nstart = 10){
  set.seed(123)
  METHODS = c("euclidean", "spherical")
  method = pmatch(method, METHODS)
  func <- if (method == 1L) kmeans else skmeans
  
  if (stage_class == 'profile'){
    ranks <- input[, append('ID', cols_paste('Avg Rank'))]
    speed2median <- input[, append('ID', cols_paste('Avg Avg Speed Rel to Median'))]
  }
  else{
    rank_cols <- median_cols <- c()
    for (col_name in colnames(input))
      if (grepl('Avg Rank', col_name) & 
          !grepl('Norm', col_name) & 
          !grepl('Total', col_name))
        rank_cols <- append(rank_cols, col_name)
      else if (grepl('Avg Avg Speed Rel to Median', col_name) & 
               !grepl('Total', col_name))
        median_cols <- append(median_cols, col_name)
    ranks <- input[, append('ID', rank_cols)]
    speed2median <- input[, append('ID', median_cols)]
  }
  ncols <- ncol(ranks)
 
  if (normalize){
    ranks_norm <- data.frame()
    median_norm <- data.frame()
    for (i in 1:nrow(ranks)){
      ranks_norm <- rbind(ranks_norm,
                          vector_normalize(as.numeric(ranks[i, 2:ncols])))
    }
    for (i in 1:nrow(speed2median)){
      median_norm <- rbind(median_norm,
                           vector_normalize(as.numeric(speed2median[i, 2:ncols])))
    }
    ranks[, 2:ncols] <- ranks_norm
    speed2median[, 2:ncols] <- median_norm
  }
  
  # 1. Calculate Hopkins Statistic
  if (hopkins){
    ranks_hpkins <- get_clust_tendency(data = ranks[, 2:ncols],
                                       n = round(nrow(ranks)/10),
                                       graph = FALSE)$hopkins_stat
    median_hpkins <- get_clust_tendency(data = speed2median[, 2:ncols],
                                        n = round(nrow(speed2median)/10),
                                        graph = FALSE)$hopkins_stat
    if (ranks_hpkins < HOPKINS_THRESHOLD){
      print("No deviance from randomness for average rank data")
      return()
    }else if (median_hpkins < HOPKINS_THRESHOLD){
      print("No deviance from randomness for average speed relative to median data")
      return()
    }
  }else{
    ranks_hpkins <- NULL
    median_hpkins <- NULL
  }
  
  # 2. Calculate the optimal number of clusters
  # 2.0 Calculate the dissimilarity object
  if (method == 1L){
    ranks_dist <- dist(ranks[, 2:ncols], method = "euclid", diag = FALSE, upper = FALSE)
    median_dist <- dist(speed2median[, 2:ncols], method = "euclid", diag = FALSE, upper = FALSE)
  }
  else{
    ranks_dist <- as.dist(skmeans_xdist(as.matrix(ranks[, 2:ncols])))
    median_dist <- as.dist(skmeans_xdist(as.matrix(speed2median[, 2:ncols])))
  }
  # 2.1 WSS (Elbow) method
  if (method == 1L){
    show(fviz_nbclust(x = ranks[, 2:ncols], FUNcluster = kmeans, method = "wss", diss = ranks_dist,
                      k.max = 10, verbose = FALSE, print.summary = FALSE) +
           ggtitle("Clustering by Average Rank"))
    show(fviz_nbclust(x = speed2median[, 2:ncols], FUNcluster = kmeans, method = "wss", diss = median_dist,
                      k.max = 10, verbose = FALSE, print.summary = FALSE) +
           ggtitle("Clustering by Average Average Speed Relative to Median"))
  }
  # 2.2 Silhouette coefficient
  show(fviz_nbclust(x = ranks[, 2:ncols], FUNcluster = func, method = "silhouette", diss = ranks_dist,
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Rank"))
  show(fviz_nbclust(x = speed2median[, 2:ncols], FUNcluster = func, method = "silhouette", diss = median_dist,
                    k.max = 10, verbose = FALSE, print.summary = FALSE) +
         ggtitle("Clustering by Average Average Speed Relative to Median"))
  # 2.3 Gap statistic
  if (method == 1L){
    show(fviz_nbclust(x = ranks[, 2:ncols], FUNcluster = kmeans, method = "gap_stat",
                      k.max = 10, verbose = FALSE, print.summary = FALSE) +
           ggtitle("Clustering by Average Rank"))
    show(fviz_nbclust(x = speed2median[, 2:ncols], FUNcluster = kmeans, method = "gap_stat",
                      k.max = 10, verbose = FALSE, print.summary = FALSE) +
           ggtitle("Clustering by Average Average Speed Relative to Median"))
  }
  
  confirm <- "n"
  while (confirm == "n"){
    ranks_optimal_k <- as.integer(readline(
      "Determine the optimal number of clusters for clustering by rank: "
      ))
    median_optimal_k <- as.integer(readline(
      "Determine the optimal number of clusters for clustering by median: "
      ))
    while (confirm != "y" ){
      print("You set the optimal number for rank and median to: ")
      print(c(ranks_optimal_k, median_optimal_k))
      confirm <- readline("Confirm it by pressing 'y', or press 'n' to re-set: ")
    }
  }
  
  # 3. Do clustering according to the optimal number of clusters
  if (method == 1L){
    ranks_kmeans <- kmeans(ranks[, 2:ncols], centers = ranks_optimal_k, iter.max = maxiter, nstart = nstart)
    median_kmeans <- kmeans(speed2median[, 2:ncols], centers = median_optimal_k, iter.max = maxiter, nstart = nstart)
  }
  else{
    ranks_kmeans <- skmeans(as.matrix(ranks[, 2:ncols]), k = ranks_optimal_k)
    median_kmeans <- skmeans(as.matrix(speed2median[, 2:ncols]), k = median_optimal_k)
    ranks_kmeans$data <- ranks[, 2:ncols]
    median_kmeans$data <- speed2median[, 2:ncols]
  }
  
  # 4. Examine the clustering results
  # 4.1 Visual inspection
  show(fviz_cluster(ranks_kmeans, ranks[, 2:ncols], geom = "point", 
                    repel = TRUE, stand = FALSE, show.clust.cent = TRUE, 
                    ellipse.type = "convex", main = "Clustering by Average Rank"))
  show(fviz_cluster(median_kmeans, speed2median[, 2:ncols], geom = "point", 
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
  list('model' = METHODS[method],
       'data' = list('ranks' = ranks, 'speed2median' = speed2median), 
       'Hopkins statistic' = list('ranks' = ranks_hpkins, 'speed2median' = median_hpkins),
       'optimal k' = list('ranks' = ranks_optimal_k, 'speed2median' = median_optimal_k),
       'k-means model' = list('ranks' = ranks_kmeans, 'speed2median' = median_kmeans),
       'silhouette' = list('ranks' = ranks_sil, 'speed2median' = median_sil))
}