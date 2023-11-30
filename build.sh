DATASET_CONTAINER="dataset"
sudo docker build . -t $DATASET_CONTAINER
PWD=$(pwd)

# Stop and delete the container if it exists
if [ "$(sudo docker ps -a -q -f name=$DATASET_CONTAINER)" ]; then
    if [ "$(sudo docker ps -aq -f status=running -f name=$DATASET_CONTAINER)" ]; then
        # cleanup
        sudo docker stop $DATASET_CONTAINER
    fi

    # delete container
    sudo docker rm $DATASET_CONTAINER
fi

# Configure the container runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo docker run --gpus all -d --name $DATASET_CONTAINER --restart unless-stopped $DATASET_CONTAINER nvidia-smi
sudo docker ps
sudo docker logs $DATASET_CONTAINER