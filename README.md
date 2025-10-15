# App Builder API

A FastAPI-based service that builds, deploys, and updates applications based on user requests. It integrates with GitHub for repository management and deployment.

## Features

- **API Endpoints**: Handle build and update requests
- **GitHub Integration**: Automatically create repositories and enable GitHub Pages
- **Authentication**: Secure API with secret key authentication
- **Task Management**: Support for multiple rounds of evaluation

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Project1-TDS
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```env
   GITHUB_TOKEN=your_github_token_here
   SECRET_KEY=your_secure_secret_here
   PORT=8000
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Build App
- **POST** `/api/build`
  - Request body: JSON with app specifications
  - Response: App deployment details

## Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token with repo and workflow permissions
- `SECRET_KEY`: Secret key for API authentication
- `PORT`: Port for the FastAPI server

## Development

### Running Tests
```bash
pytest
```

### Linting
```bash
flake8 .
```

## License

MIT
