import matplotlib.pyplot as plt
import numpy as np
import random


## 0. Create a Point class and some usefull functions
class Point:
    ## A point is created by calling Point(x,y)
    def __init__(self, x, y):
        self.x = x
        self.y = y
        return

    def plot_self(self, axes, marker, color):
        ## Plots itself on a given matplotlib axes with a certain color
        axes.plot(self.x, self.y, marker=marker, color=color)

def distance(point1, point2):
    ## Returns the distance between point1 and point2
    return np.sqrt( (point2.x - point1.x)**2 + (point2.y - point1.y)**2 )

def random_point(a, b):
    ## Returns a point object with x,y values between a and b.
    return Point(random.uniform(a,b), random.uniform(a,b))

def cluster_mean(cluster):
    ## Returns the mean value of a cluster of points
    x_sum = 0
    y_sum = 0
    for point in cluster:
        x_sum += point.x ## a += b represents a = a + b
        y_sum += point.y
    x_avg = x_sum / len(cluster)
    y_avg = y_sum / len(cluster)
    return Point(x_avg, y_avg)

## 1. Create a random set of 1000 data points
n_points = 1000
points = [ ]
for i in range(n_points):
    points.append(random_point(2,8)) # This will add a random point with x,y values between 2 and 8 to our array of points

## 2. Generate our first set of 7 random cluster centers
n_clusters = 7
means = [ ]
for cluster_id in range(n_clusters):
    means.append(random_point(2,8))

## 3. Perform clustering
n_iterations = 50
for i in range(n_iterations): ## Iterate the process 50 times
    clusters = [ ] ## Clear our clusters before each iteration
    for cluster_id in range(n_clusters):
        clusters.append( [ ] ) ## Create an empty cluster for as many clusters as we have
    for point in points: ## Iterate over every data point
        dists = [ ] 
        for mean in means: 
            dists.append(distance(point, mean)) ## Calculates the distance from the current point to each mean
        closest_mean_index = dists.index(min(dists)) ## Returns the index of the smallest distance
        clusters[closest_mean_index].append(point) ## Add the point to the appropriate cluster
    for cluster_id in range(n_clusters): 
        means[cluster_id] = cluster_mean(clusters[cluster_id]) ## Calculate new mean for each cluster

## 4. Plot your clusters
colors = ["blue", "orange", "red", "green", "black", "yellow", "cyan"] ## Add more colors here for each cluster you have
figure, axes = plt.subplots(1,1) ## Create our figure and axes objects
for cluster_id in range(n_clusters): ## Iterate over each cluster
    for point in clusters[cluster_id]: ## Iterate over each point in the cluster
        point.plot_self(axes=axes, marker="o", color=colors[cluster_id])
    means[cluster_id].plot_self(axes=axes, marker="x", color=colors[cluster_id])
    
plt.grid() ## Creates a grid on the plot figure. Visual aesthetics only.
plt.show() ## Show the plot




