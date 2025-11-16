# Web Application with HTTP and Socket Servers

Simple web application without web frameworks featuring HTTP server and Socket server for storing messages in MongoDB.

## Features

- HTTP server on port 3000
- Socket server on port 5001 (TCP)
- MongoDB integration for message storage
- Docker and Docker Compose configuration
- Static file serving (CSS, images)
- 404 error handling with custom error page

## Requirements

- Docker
- Docker Compose

## Running

```bash
docker-compose up --build
```

Application will be available at http://localhost:3000

## Project Structure

```
goit-cs-hw-06/
├── main.py                 # HTTP and Socket servers
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yaml     # Docker Compose configuration
└── front-init/             # Frontend files
    ├── index.html
    ├── message.html
    ├── error.html
    ├── style.css
    └── logo.png
```

## Architecture

**HTTP Server (port 3000)**
- Handles GET requests for HTML pages and static files
- Handles POST requests from `/message` form
- Forwards data to Socket server
- Handles 404 errors

**Socket Server (port 5001)**
- Receives data via TCP socket
- Converts JSON to dictionary
- Saves messages to MongoDB with automatic timestamp

**MongoDB**
- Database: `messages_db`
- Collection: `messages`
- Document format:
  ```json
  {
    "date": "2022-10-29 20:20:58.020261",
    "username": "krabaton",
    "message": "First message"
  }
  ```

## Usage

### Sending a message

1. Open http://localhost:3000/message.html
2. Fill in the form (nickname and message)
3. Click "Send"

### Viewing saved messages

```bash
docker-compose exec mongodb mongosh messages_db --eval "db.messages.find().pretty()"
```

## Docker Commands

```bash
# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
