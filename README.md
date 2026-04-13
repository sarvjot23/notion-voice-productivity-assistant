# notion-voice-productivity-assistant

Voice-driven productivity assistant to manage and sync tasks across Notion, Google Calendar, and Todoist.

## Key Features

- **Voice-Activated**: Use voice commands to create and manage tasks and events.
- **Integration**: Sync seamlessly with Notion, Google Calendar, and Todoist.
- **Memory Store**: Retains context and stores user data for personalized assistance.
- **Health Check**: Built-in health check endpoint for server status monitoring.

## Tech Stack

- **Languages**: Python, JavaScript, Markdown, JSON, YAML
- **Frameworks & Libraries**: FastAPI
- **Infrastructure & Tools**: Docker, Docker Compose

## Prerequisites & Installation

Ensure you have Docker and Docker Compose installed on your machine. Follow these steps to get started:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/notion-voice-productivity-assistant.git
   cd notion-voice-productivity-assistant
   ```

2. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

3. The service should now be running on your local machine.

## Usage / How to Run

To start using the Voice Productivity Assistant, follow these steps:

1. Access the frontend interface by navigating to `http://localhost:8000` in your web browser.
2. Use voice commands to interact with the service.
3. Monitor the server's health status by accessing the endpoint at `http://localhost:8000/health`.

## What I Learned

Through this project, I gained practical experience with:

- Setting up a Python web application using FastAPI.
- Integrating third-party services like Notion, Google Calendar, and Todoist.
- Managing dependencies and containerizing applications with Docker.
- Structuring a project directory for maintainability and scalability.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.