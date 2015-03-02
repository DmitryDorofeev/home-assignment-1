#!/usr/bin/env bash

wget -q -O - http://tarantool.org/dist/public.key | apt-key add -
echo "deb http://tarantool.org/dist/stable/ubuntu/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/tarantool.list

apt-get update

apt-get install -y \
    build-essential \
    libcurl4-openssl-dev \
    python-dev \
    python-pip \
    tarantool-lts

pip install -Ur /home/vagrant/home-assignment-1/requirements.txt

cp /home/vagrant/home-assignment-1/provision/tarantool.cfg /etc/tarantool/instances.enabled/tarantool.cfg
cp /home/vagrant/home-assignment-1/provision/init.lua /usr/share/tarantool/lua/init.lua

service tarantool-lts restart
