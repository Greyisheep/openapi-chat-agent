# OpenAPI Chat Agent API - Postman Collection

This Postman collection contains all the API endpoints for the OpenAPI Conversational Agent Platform. The collection is organized into logical groups for easy navigation and testing.

## 📁 Collection Structure

The collection is organized into the following folders:

### 🔍 Health
- **Health Check** - Verify API status

### 🔐 Authentication
- **Register User** - Create a new user account
- **Login (Form)** - OAuth2 form-based login
- **Login (JSON)** - JSON-based login
- **Get Current User** - Retrieve user information
- **Update Profile** - Update user profile
- **Change Password** - Change user password
- **Set Gemini API Key** - Configure Gemini API key
- **Get API Key Status** - Check API key configuration
- **Remove Gemini API Key** - Remove Gemini API key
- **Generate Platform API Key** - Generate platform API key
- **Logout** - Revoke authentication token

### 🤖 Agents
- **Create Agent** - Create agent with OpenAPI spec
- **Create Agent from URL** - Create agent from OpenAPI URL
- **List Agents** - List user's agents
- **Get Agent** - Get specific agent details
- **Chat with Agent** - Send message to agent
- **Get Agent Tools** - List agent's available tools
- **Get Agent Conversations** - Get conversation history
- **Get Tool Executions** - Get tool execution history
- **Delete Agent** - Delete an agent

### 🏪 Marketplace
- **List Templates** - Browse available templates
- **List Templates with Filters** - Filter templates by category/featured/search
- **Get Template** - Get specific template details
- **List Categories** - Browse template categories
- **Create Agent from Template** - Create agent from marketplace template

### 🏠 Root
- **Root Endpoint** - Platform information

## 🚀 Getting Started

### 1. Import the Collection

1. Download the `OpenAPI_Chat_Agent_API.postman_collection.json` file
2. Open Postman
3. Click "Import" and select the JSON file
4. The collection will be imported with all endpoints

### 2. Configure Environment Variables

The collection uses the following environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `base_url` | API base URL | `http://localhost:8000` |
| `access_token` | JWT access token | (empty) |
| `agent_id` | Agent ID for agent requests | (empty) |
| `template_id` | Template ID for marketplace requests | (empty) |

**To set up environment variables:**

1. In Postman, click the "Environment" dropdown (top right)
2. Click "Add" to create a new environment
3. Add the variables above with appropriate values
4. Save the environment

### 3. Authentication Flow

#### Step 1: Register a User
1. Use the **"Register User"** request
2. Update the request body with your details:
```json
{
  "email": "your-email@example.com",
  "username": "your-username",
  "password": "SecurePass123!",
  "full_name": "Your Full Name"
}
```

#### Step 2: Login
1. Use either **"Login (JSON)"** or **"Login (Form)"** request
2. For JSON login, use:
```json
{
  "email_or_username": "your-email@example.com",
  "password": "SecurePass123!"
}
```

#### Step 3: Set Access Token
1. Copy the `access_token` from the login response
2. Set the `access_token` environment variable with this value
3. All subsequent authenticated requests will use this token

### 4. Using the Collection

#### Testing Health
Start with the **Health Check** to verify the API is running.

#### Creating an Agent
1. **Option A: Create from OpenAPI Spec**
   - Use **"Create Agent"** with a complete OpenAPI specification
   - Include your API key and base URL

2. **Option B: Create from URL**
   - Use **"Create Agent from URL"** with a public OpenAPI spec URL
   - Example: `https://petstore3.swagger.io/api/v3/openapi.json`

3. **Option C: Create from Marketplace Template**
   - Browse templates using **"List Templates"**
   - Get template details with **"Get Template"**
   - Create agent using **"Create Agent from Template"**

#### Chatting with Agents
1. Get your agent ID from the create response
2. Set the `agent_id` environment variable
3. Use **"Chat with Agent"** to send messages
4. Optionally include a `conversation_id` for conversation continuity

## 📝 Request Examples

### Create Agent Example
```json
{
  "name": "GitHub Assistant",
  "openapi_spec_url": "https://api.github.com/openapi.json",
  "user_api_key": "ghp_your_github_token",
  "api_base_url": "https://api.github.com",
  "user_instructions": "You are a helpful GitHub assistant. Help users manage repositories, issues, and pull requests."
}
```

### Chat Example
```json
{
  "message": "Can you help me create a new repository?",
  "conversation_id": "optional-conversation-id"
}
```

### Create from Template Example
```json
{
  "agent_name": "My Custom GitHub Bot",
  "api_key": "ghp_your_github_token",
  "custom_instructions": "Focus on helping with open source projects and code reviews."
}
```

## 🔧 Configuration

### Setting Up Gemini API Key
1. Get a Gemini API key from Google AI Studio
2. Use **"Set Gemini API Key"** to configure it
3. This enables AI-powered conversations with your agents

### Platform API Key
1. Use **"Generate Platform API Key"** to create a platform key
2. This key can be used for external integrations
3. Store it securely for external API access

## 🧪 Testing Workflows

### Complete User Journey
1. **Register** → Create account
2. **Login** → Get access token
3. **Set Gemini API Key** → Enable AI features
4. **List Templates** → Browse available agents
5. **Create Agent from Template** → Deploy an agent
6. **Chat with Agent** → Test the agent
7. **Get Agent Tools** → See available capabilities
8. **Get Conversations** → Review chat history

### Agent Management
1. **Create Agent** → Deploy custom agent
2. **List Agents** → View all agents
3. **Get Agent** → Check agent status
4. **Chat with Agent** → Interact with agent
5. **Get Tool Executions** → Monitor agent activity
6. **Delete Agent** → Clean up when done

## 🔍 Troubleshooting

### Common Issues

**401 Unauthorized**
- Check if `access_token` is set correctly
- Verify token hasn't expired (30 minutes by default)
- Re-login if needed

**400 Bad Request**
- Check request body format
- Verify required fields are provided
- Check password strength requirements

**404 Not Found**
- Verify `agent_id` or `template_id` is correct
- Check if the resource exists
- Ensure you have permission to access it

**500 Internal Server Error**
- Check server logs
- Verify database connection
- Ensure all required services are running

### Environment Setup
Make sure your API server is running on the configured `base_url`. The default is `http://localhost:8000`.

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Postman Learning Center](https://learning.postman.com/)
- [OpenAPI Specification](https://swagger.io/specification/)

## 🤖 Automation Features

### Collection Secrets & Variables

The collection includes several automation features:

#### **Auto-Extraction Variables**
- `access_token` - Automatically extracted from login responses
- `agent_id` - Automatically extracted from agent creation responses  
- `template_id` - Automatically extracted from template responses
- `conversation_id` - For chat continuity

#### **Test User Variables**
- `test_user_email` - Test user email for automation
- `test_user_password` - Test user password (marked as secret)
- `test_user_username` - Test user username

#### **API Key Variables**
- `gemini_api_key` - Gemini API key for AI features (secret)
- `sample_api_key` - Sample API key for testing (secret)
- `platform_api_key` - Platform API key for external use

### Pre-request Scripts

The collection includes automatic pre-request scripts that:
- Auto-set `Content-Type: application/json` for JSON requests
- Auto-add `Authorization: Bearer {{access_token}}` for protected endpoints
- Handle authentication automatically

### Test Scripts

Each request includes test scripts that:
- Auto-extract tokens and IDs from responses
- Validate response structure and timing
- Log response details for debugging
- Set environment variables automatically

## 🚀 CI/CD Integration

### Newman Test Runner

Use the included `postman-tests.js` script for automated testing:

```bash
# Install dependencies
npm install -g newman newman-reporter-html newman-reporter-junit

# Run tests locally
node postman-tests.js

# Run tests against different environments
node postman-tests.js --base-url https://staging-api.example.com
node postman-tests.js --base-url https://api.example.com

# Run with different reporters
node postman-tests.js --reporters cli,html,junit

# Stop on first failure
node postman-tests.js --bail
```

### GitHub Actions

The collection includes a GitHub Actions workflow (`.github/workflows/postman-tests.yml`) that:

- Runs on push/PR to main/develop branches
- Tests against multiple Node.js versions
- Supports manual triggering with environment selection
- Uploads test results as artifacts
- Comments test results on PRs
- Integrates with GitHub Secrets for API keys

### Environment Setup

1. **Import Environment**: Import `OpenAPI_Chat_Agent_Environment.postman_environment.json`
2. **Set Secrets**: Configure sensitive variables like API keys
3. **Update Base URL**: Change `base_url` for your environment
4. **Test User**: Update test user credentials if needed

### Package.json Scripts

```json
{
  "scripts": {
    "test": "node postman-tests.js",
    "test:local": "node postman-tests.js --base-url http://localhost:8000",
    "test:staging": "node postman-tests.js --base-url https://staging-api.example.com",
    "test:production": "node postman-tests.js --base-url https://api.example.com",
    "test:ci": "node postman-tests.js --reporters cli,json --bail"
  }
}
```

## 🔐 Security Best Practices

### Secrets Management

1. **Mark sensitive variables as secrets** in Postman
2. **Use environment variables** for different environments
3. **Never commit API keys** to version control
4. **Use GitHub Secrets** for CI/CD automation

### Environment Variables

| Variable | Type | Description |
|----------|------|-------------|
| `access_token` | Secret | JWT token (auto-extracted) |
| `test_user_password` | Secret | Test user password |
| `gemini_api_key` | Secret | Gemini API key |
| `sample_api_key` | Secret | Sample API key |
| `platform_api_key` | Secret | Platform API key |

## 📊 Test Reporting

### Available Reporters

- **CLI**: Console output with colored results
- **JSON**: Machine-readable test results
- **HTML**: Beautiful HTML report with charts
- **JUnit**: XML format for CI/CD integration

### Example Output

```bash
🚀 Starting Postman Collection Tests
📁 Collection: OpenAPI_Chat_Agent_API.postman_collection.json
🌍 Environment: OpenAPI_Chat_Agent_Environment.postman_environment.json
🔗 Base URL: http://localhost:8000
📊 Reporters: cli,json,html
⏱️  Delay: 1000ms
🛑 Bail on failure: true

📊 Test Results Summary:
✅ Passed: 45
❌ Failed: 0
⏭️  Skipped: 0
📝 Total: 45
⏱️  Duration: 52340ms

🎉 All tests passed!
```

## 🤝 Contributing

To update this collection:
1. Modify the JSON file
2. Test all endpoints
3. Update this README if needed
4. Share the updated collection

### Adding New Endpoints

1. Add the endpoint to the collection
2. Include proper test scripts for auto-extraction
3. Update environment variables if needed
4. Test the automation flow
5. Update documentation

---

**Happy Testing! 🚀**
