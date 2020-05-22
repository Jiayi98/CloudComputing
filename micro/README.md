## Assignment 5: Microservice architecture on Kubernetes

Re-architecture the movie application into microservice style. There will be two microservices - one corresponding to the application code and another corresponding to the database. Essentially we deploy the application and its database both on Kubernetes. Modern cloud-native applications are being built in this fashion where stateful services like databases are also run as containers.
Refer to the Wordpress deployment on Kubernetes for reference:
https://kubernetes.io/docs/tutorials/stateful-application/mysql-wordpress-persistent-volume/
database will be running on Kubernetes itself. It won’t be directly accessible outside of the cluster. Expose your database on ClusterIP type of Service.
