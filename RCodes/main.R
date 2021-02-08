source('kmeans.R')

grand_sc_kmeans <- kmeans_sc(grand_sc_fltrd, hopkins = TRUE)
save.image()
