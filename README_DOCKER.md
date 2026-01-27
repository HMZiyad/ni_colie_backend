# Docker Setup

This project uses Docker and Docker Compose for easy deployment and development.

## Prerequisities

- Docker Desktop installed and running.

## Running the Project

1.  Build and run the containers:

    ```bash
    docker-compose up --build
    ```

2.  The application will be available at [http://localhost:8000](http://localhost:8000).

3.  To stop the containers:

    ```bash
    docker-compose down
    ```

## Running Commands

To run Django management commands (like migrations or creating a superuser), use `docker-compose exec`:

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run tests
docker-compose exec web python manage.py test
```

## Services

-   **web**: The Django application running with Daphne.
-   **db**: Postgres 15 database.
-   **redis**: Redis 7 for Django Channels.
-   **pgadmin**: Web interface for managing the database (available at :5050).

## pgAdmin Setup

1.  Start the services: `docker-compose up -d`
2.  Open [http://localhost:5050](http://localhost:5050)
3.  Login with:
    -   **Email:** `admin@admin.com`
    -   **Password:** `root`
4.  Right-click **Servers** > **Register** > **Server...**
5.  **General** tab: Name it `Local Docker DB` (or similar).
6.  **Connection** tab:
    -   **Host name/address:** `db`
    -   **Port:** `5432`
    -   **Maintenance database:** `postgres`
    -   **Username:** `postgres`
    -   **Password:** `postgres`
7.  Click **Save**. You can now view your database tables under `Schemas > public > Tables`.
