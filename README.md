# InnerWebBlueprint.com Wordpress Website Factory

iwb-wp-website-factory

---

This repository is the 'build' directory for a docker image named:

iwbp/iwb-wp-website-factory

This image is based off the offical 'wordpress' image and add a distributed cloud storage layer using Storj. It also includes some 'backend' scripting to handle automated backup and restores using the distributed cloud storage layer.

It automatically backs up a wordpress site, files and database, to Storj. The image also restores a wordpress site to it's last backed up state on a newly deployed docker container, pulling from Storj encrypted persistent distributed storage.

I originally put this together to host on the Akash distributed compute cloud, however this will work pretty much anywhere you can run a docker image. Linode is my preferred choice as it currently outperforms almost all providers on Akash. I hope that will eventually change.

You can use the image, without building it yourself, it's up on Docker Hub.

see: http://www.innerwebblueprint.com/iwb-wp-website-factory for more explanation on how to use the image, why I made it, the problems it solves, and how it might benefit you.

This repository includes everything required to build the image. It also includes an example docker-compose.yml file with notes on private enviornment variables required.
