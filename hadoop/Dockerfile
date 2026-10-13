# Image Hadoop officielle + python3 (nécessaire pour le job Hadoop Streaming mapper.py / reducer.py).
# CentOS 7 est en fin de vie : les dépôts yum sont redirigés vers vault.centos.org.
FROM apache/hadoop:3.4.1
USER root
RUN sed -i -e 's/^mirrorlist=/#mirrorlist=/' \
           -e 's|^#\?baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|' /etc/yum.repos.d/CentOS-*.repo \
 && yum install -y python3 \
 && yum clean all
USER hadoop
