# cava-realtime

Home of the Interactive Oceans Realtime Data Service

## Run with docker-compose

1. Build the images

    ```bash
    docker-compose -f resources/docker/docker-compose.yaml build
    ```

2. Set OOI Username and Token

    ```bash
    export OOI_USERNAME=MyUser
    export OOI_TOKEN=AS3cret
    ```

3. Bring up all the components

    ```bash
    docker-compose -f resources/docker/docker-compose.yaml up
    ```

4. Go to http://localhost:8080/realtime/ to see the API Service
5. Stop the components and tear down. (Ctrl+C on the terminal)

    ```bash
    docker-compose -f resources/docker/docker-compose.yaml down
    ```
