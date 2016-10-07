import random
from matplotlib import pyplot as plt
from matplotlib import ticker as mtick


def make_cluster(xmin,ymin,xmax,ymax,npts):
    xout = []
    yout = []
    for i in range(npts):
        xout.append(random.uniform(xmin,xmax))
        yout.append(random.uniform(ymin,ymax))
    return xout, yout

c1 = make_cluster(1,.2,2,2,35)
c2 = make_cluster(3,0.3,4,2,32)
c3 = make_cluster(1,3,3,5,37)

loc = mtick.MultipleLocator(base=0.5)
fig,ax = plt.subplots()
ax.plot(c1[0],c1[1],"ro",c2[0],c2[1],"go",c3[0],c3[1],"bo")
ax.xaxis.set_major_locator(loc)
ax.yaxis.set_major_locator(loc)
plt.axis([0,5,0,6])
ax.grid()
plt.title("Clustering Example")
plt.legend(["Cluster 1","Cluster 2","Cluster 3"])
plt.show()