# filesystem-mcp-server Developer Cheatsheet

**Goal**: This project aims to create a Model Context Protocol (MCP) server providing robust, platform-agnostic file system capabilities. Key features include reading files, writing files, updating files with targeted changes, managing a default working directory for the session, and comprehensive HTTP/STDIO transport support.

This cheatsheet provides quick references for common patterns and utilities within the `filesystem-mcp-server` codebase.

## Project Structure

**IMPORTANT**: All paths are relative to the project root. There is NO `src/` directory.

```
filesystem-mcp-server/
├── config/
│   └── index.ts              # Configuration with Zod validation
├── mcp-server/
│   ├── server.ts             # Server initialization and tool registration
│   ├── state.ts              # Session state management
│   ├── tools/                # Tool implementations
│   │   ├── readFile/
│   │   │   ├── index.ts
│   │   │   ├── readFileLogic.ts
│   │   │   └── registration.ts
│   │   └── [otherTools]/
│   └── transports/
│       ├── stdioTransport.ts
│       ├── httpTransport.ts
│       └── authentication/
│           └── authMiddleware.ts
├── types-global/
│   ├── errors.ts             # McpError class and BaseErrorCode enum
│   ├── mcp.ts               # MCP response types
│   └── tool.ts              # Tool interfaces
├── utils/
│   ├── internal/
│   │   ├── errorHandler.ts   # ErrorHandler.tryCatch and error management
│   │   ├── logger.ts         # Structured logging with Winston
│   │   └── requestContext.ts # Request context management
│   ├── metrics/
│   │   └── tokenCounter.ts   # Token counting utilities
│   ├── parsing/
│   │   ├── dateParser.ts     # Natural language date parsing
│   │   └── jsonParser.ts     # Partial JSON parsing
│   ├── security/
│   │   ├── idGenerator.ts    # UUID and prefixed ID generation
│   │   ├── rateLimiter.ts    # Rate limiting utilities
│   │   └── sanitization.ts  # Input sanitization
│   └── index.ts             # Barrel export for all utilities
└── index.ts                 # Main application entry point
```

## Core Utilities Integration

### 1. Logging (`utils/internal/logger.ts`)

- **Purpose**: Structured logging with Winston, file rotation, and MCP notification support.
- **Usage**: Import the singleton `logger` instance and initialize it in your application startup.

```typescript
import { logger } from './utils/internal/logger.js';
import { requestContextService } from './utils/internal/requestContext.js';

// Initialize logger (typically in main startup)
await logger.initialize('debug'); // or 'info', 'warn', 'error'

// Create context for logging correlation
const context = requestContextService.createRequestContext({
  operation: 'YourOperation',
  additionalData: 'value'
});

// Log with context
logger.info("Processing request", context);
logger.debug("Detailed step info", { ...context, data: someData });
logger.warning("Potential issue detected", context);
logger.error("An error occurred", context); // Error object as second param if needed
```

- **Key Features**:
  - File logging with rotation (combined.log, error.log, etc.)
  - Console logging only in debug mode when stdout is TTY
  - MCP notification support for sending logs via MCP protocol
  - Context-aware logging with request correlation

### 2. Error Handling (`types-global/errors.ts`, `utils/internal/errorHandler.ts`)

- **Purpose**: Standardized error handling with `McpError` class and `ErrorHandler.tryCatch` wrapper.
- **Usage**: Use `ErrorHandler.tryCatch` to wrap operations and `McpError` for specific errors.

```typescript
import { ErrorHandler } from './utils/internal/errorHandler.js';
import { McpError, BaseErrorCode } from './types-global/errors.js';
import { RequestContext } from './utils/internal/requestContext.js';

async function performTask(input: any, context: RequestContext) {
  return await ErrorHandler.tryCatch(
    async () => {
      if (!input) {
        throw new McpError(
          BaseErrorCode.VALIDATION_ERROR, 
          "Input cannot be empty", 
          { ...context, inputReceived: input }
        );
      }
      
      const result = await someAsyncOperation(input);
      return result;
    },
    {
      operation: 'performTask',
      context: context,
      input: input, // Automatically sanitized for logging
      errorCode: BaseErrorCode.INTERNAL_ERROR // Default if unexpected error
    }
  );
}
```

- **Error Codes**: Use `BaseErrorCode` enum values:
  - `VALIDATION_ERROR`: Invalid input/parameters
  - `NOT_FOUND`: Resource not found
  - `UNAUTHORIZED`: Authentication required
  - `FORBIDDEN`: Access denied
  - `INTERNAL_ERROR`: Unexpected server error
  - `RATE_LIMITED`: Rate limit exceeded
  - `CONFIGURATION_ERROR`: Config issues

### 3. Request Context (`utils/internal/requestContext.ts`)

- **Purpose**: Track operations with unique IDs and timestamps for correlation.
- **Usage**: Create context at operation boundaries and pass through call chains.

```typescript
import { requestContextService, RequestContext } from './utils/internal/requestContext.js';

// Configure the service (typically at startup)
requestContextService.configure({
  appName: 'filesystem-mcp-server',
  appVersion: '1.0.1',
  environment: 'development'
});

// Create context at entry points
const context: RequestContext = requestContextService.createRequestContext({
  operation: 'HandleToolCall',
  toolName: 'read_file',
  userInput: sanitizedInput
});

// Pass context through function calls
await processFile(filePath, context);

function processFile(path: string, parentContext: RequestContext) {
  const subContext = { ...parentContext, subOperation: 'ValidatePath' };
  // Use subContext for logging and errors in this function
}
```

### 4. Server State (`mcp-server/state.ts`)

- **Purpose**: Manages session-specific state, primarily the default filesystem path.
- **Usage**: Import `serverState` singleton for path resolution.

```typescript
import { serverState } from './mcp-server/state.js';
import { RequestContext } from './utils/internal/requestContext.js';

// Set default path (typically by setFilesystemDefault tool)
try {
  serverState.setDefaultFilesystemPath('/Users/casey/Documents', context);
} catch (error) {
  // Handle McpError for invalid paths
}

// Resolve paths in tool logic
try {
  const absolutePath = serverState.resolvePath('data/file.txt', context);
  // absolutePath will be resolved against the default if relative
} catch (error) {
  // Handle McpError if no default set for relative path
}

// Get current default
const currentDefault = serverState.getDefaultFilesystemPath(); // null if not set

// Clear default
serverState.clearDefaultFilesystemPath(context);
```

### 5. Sanitization (`utils/security/sanitization.ts`)

- **Purpose**: Input validation and sanitization for security and data integrity.
- **Usage**: Import `sanitization` singleton for various sanitization needs.

```typescript
import { sanitization } from './utils/security/sanitization.js';

// Sanitize file paths (prevents traversal)
try {
  const pathInfo = sanitization.sanitizePath(userPath, {
    rootDir: '/safe/directory',
    allowAbsolute: false,
    toPosix: true
  });
  const safePath = pathInfo.sanitizedPath;
} catch (error) {
  // Handle McpError for invalid paths
}

// Sanitize HTML content
const safeHtml = sanitization.sanitizeHtml('<script>alert("xss")</script><p>Safe</p>');
// Result: "<p>Safe</p>"

// Sanitize for logging (redacts sensitive fields)
const logSafeData = sanitization.sanitizeForLogging({
  user: 'admin',
  password: 'secret123',  // Will become '[REDACTED]'
  token: 'abc123',        // Will become '[REDACTED]'
  safeField: 'value'      // Remains unchanged
});

// Sanitize numbers with validation and clamping
const num = sanitization.sanitizeNumber('123.45', 0, 1000); // 123.45
```

### 6. ID Generation (`utils/security/idGenerator.ts`)

- **Purpose**: Generate UUIDs and prefixed IDs for correlation and entity identification.
- **Usage**: Use `generateUUID()` for simple UUIDs or `idGenerator` for prefixed IDs.

```typescript
import { generateUUID, idGenerator } from './utils/security/idGenerator.js';

// Simple UUID generation
const requestId = generateUUID();

// Prefixed ID generation (configure first)
idGenerator.setEntityPrefixes({
  request: 'REQ',
  operation: 'OP',
  session: 'SESS'
});

const reqId = idGenerator.generateForEntity('request'); // "REQ_A6B3J0"
const opId = idGenerator.generateForEntity('operation', { length: 8 }); // "OP_C9D4E1F2"

// Validate IDs
const isValid = idGenerator.isValid(reqId, 'request'); // true

// Get entity type from ID
const entityType = idGenerator.getEntityType('REQ_A6B3J0'); // 'request'
```

### 7. Rate Limiting (`utils/security/rateLimiter.ts`)

- **Purpose**: Control operation frequency per key to prevent abuse.
- **Usage**: Import `rateLimiter` singleton or create custom instances.

```typescript
import { rateLimiter } from './utils/security/rateLimiter.js';

// Configure rate limiter
rateLimiter.configure({
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: 100,
  skipInDevelopment: true
});

// Check rate limit (throws McpError if exceeded)
try {
  rateLimiter.check(`user_${userId}`, context);
  // Proceed with operation
} catch (error) {
  if (error instanceof McpError && error.code === BaseErrorCode.RATE_LIMITED) {
    // Handle rate limit exceeded
  }
}

// Get current status
const status = rateLimiter.getStatus(`user_${userId}`);
// { current: 5, limit: 100, remaining: 95, resetTime: 1640995200000 }
```

## Configuration System (`config/index.ts`)

The configuration system uses Zod for validation and supports comprehensive environment variables:

```typescript
import { config, environment } from './config/index.js';

// Available configuration
const serverConfig = {
  mcpServerName: config.mcpServerName,           // From MCP_SERVER_NAME or package.json
  mcpServerVersion: config.mcpServerVersion,     // From MCP_SERVER_VERSION or package.json
  logLevel: config.logLevel,                     // From MCP_LOG_LEVEL (default: "debug")
  environment: config.environment,               // From NODE_ENV (default: "development")
  mcpTransportType: config.mcpTransportType,     // From MCP_TRANSPORT_TYPE ("stdio" or "http")
  
  // HTTP transport (if enabled)
  mcpHttpPort: config.mcpHttpPort,               // From MCP_HTTP_PORT (default: 3010)
  mcpHttpHost: config.mcpHttpHost,               // From MCP_HTTP_HOST (default: "127.0.0.1")
  mcpAuthSecretKey: config.mcpAuthSecretKey,     // From MCP_AUTH_SECRET_KEY (JWT secret)
  
  // LLM integration
  llmDefaultModel: config.llmDefaultModel,       // From LLM_DEFAULT_MODEL
  openrouterApiKey: config.openrouterApiKey,     // From OPENROUTER_API_KEY
  geminiApiKey: config.geminiApiKey,             // From GEMINI_API_KEY
};
```

## Adding New Tools

### 1. Directory Structure

Create: `mcp-server/tools/yourToolName/`

### 2. Logic Implementation (`yourToolNameLogic.ts`)

```typescript
import fs from 'fs/promises';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define input schema with Zod
export const YourToolInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('File path (relative or absolute)'),
  option: z.boolean().default(false)
    .describe('Optional boolean parameter')
});

export type YourToolInput = z.infer<typeof YourToolInputSchema>;

// Define output interface
export interface YourToolOutput {
  message: string;
  result: any;
}

// Implement logic function
export const yourToolLogic = async (
  input: YourToolInput, 
  context: RequestContext
): Promise<YourToolOutput> => {
  const { path: requestedPath, option } = input;
  const logicContext = { ...context, tool: 'yourToolLogic', option };
  
  logger.debug(`Processing tool request for path: ${requestedPath}`, logicContext);
  
  // Resolve path using server state
  const absolutePath = serverState.resolvePath(requestedPath, context);
  
  try {
    // Implement your tool logic here
    const result = await fs.readFile(absolutePath, 'utf8');
    
    logger.info(`Successfully processed tool request`, { 
      ...logicContext, 
      resultLength: result.length 
    });
    
    return {
      message: `Successfully processed ${absolutePath}`,
      result: result
    };
  } catch (error: any) {
    logger.error(`Tool processing failed`, { 
      ...logicContext, 
      error: error.message,
      code: error.code 
    });
    
    if (error instanceof McpError) {
      throw error;
    }
    
    // Convert to appropriate McpError
    if (error.code === 'ENOENT') {
      throw new McpError(
        BaseErrorCode.NOT_FOUND, 
        `File not found: ${absolutePath}`, 
        { ...logicContext, requestedPath, resolvedPath: absolutePath }
      );
    }
    
    throw new McpError(
      BaseErrorCode.INTERNAL_ERROR, 
      `Failed to process file: ${error.message}`, 
      { ...logicContext, originalError: error }
    );
  }
};
```

### 3. Registration (`registration.ts`)

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  YourToolInputSchema,
  yourToolLogic
} from './yourToolNameLogic.js';

export const registerYourToolTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ 
    operation: 'RegisterYourToolTool' 
  });
  
  logger.info("Attempting to register 'your_tool' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'your_tool',
        'Description of what your tool does',
        YourToolInputSchema.shape,
        async (params, extra) => {
          // Validate input
          const validationResult = YourToolInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ 
              operation: 'YourToolValidation' 
            });
            logger.error('Invalid input parameters', { 
              ...errorContext, 
              errors: validationResult.error.errors 
            });
            throw new McpError(
              BaseErrorCode.VALIDATION_ERROR, 
              `Invalid parameters: ${validationResult.error.errors.map(e => 
                `${e.path.join('.')} - ${e.message}`
              ).join(', ')}`, 
              errorContext
            );
          }
          
          const typedParams = validationResult.data;
          const callContext = requestContextService.createRequestContext({ 
            operation: 'YourToolExecution' 
          });
          
          logger.info(`Executing 'your_tool' for: ${typedParams.path}`, callContext);

          // Execute with error handling
          const result = await ErrorHandler.tryCatch(
            () => yourToolLogic(typedParams, callContext),
            {
              operation: 'yourToolLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams),
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'your_tool'`, { 
            ...callContext, 
            resultMessage: result.message 
          });

          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      
      logger.info("'your_tool' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerYourToolTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
```

### 4. Index Export (`index.ts`)

```typescript
export { registerYourToolTool } from './registration.js';
```

### 5. Register in Server (`mcp-server/server.ts`)

```typescript
// Add import
import { registerYourToolTool } from './tools/yourToolName/index.js';

// Add to registration promises in createMcpServerInstance()
const registrationPromises = [
  registerReadFileTool(server),
  registerWriteFileTool(server),
  // ... other tools
  registerYourToolTool(server), // Add your tool here
];
```

## Transport Support

The server supports both STDIO and HTTP transports:

### STDIO Transport (Default)
- Direct stdin/stdout communication
- Typically used when launched as child process
- No authentication required (process isolation provides security)

### HTTP Transport
- RESTful API with Server-Sent Events for streaming
- JWT-based authentication via Bearer tokens
- CORS support with configurable origins
- Supports POST (requests), GET (streaming), DELETE (cleanup)

## Key Files Reference

- **Main Entry**: `index.ts` (startup, signal handling, error management)
- **Server Setup**: `mcp-server/server.ts` (MCP server creation, tool registration)
- **State Management**: `mcp-server/state.ts` (session state like default path)
- **Configuration**: `config/index.ts` (environment variables, Zod validation)
- **Error Types**: `types-global/errors.ts` (McpError, BaseErrorCode)
- **Core Utilities**: `utils/internal/` (logger, errorHandler, requestContext)
- **Security**: `utils/security/` (sanitization, rateLimiter, idGenerator)
- **Tools**: `mcp-server/tools/*/` (each tool has logic, registration, index)

## Development Tips

1. **Always use ErrorHandler.tryCatch** for async operations that might fail
2. **Pass RequestContext** through function calls for proper logging correlation
3. **Use serverState.resolvePath** for all file path resolution to respect session defaults
4. **Validate inputs with Zod** schemas before processing
5. **Sanitize sensitive data** before logging using `sanitization.sanitizeForLogging`
6. **Initialize logger** early in application startup with appropriate log level
7. **Follow the tool structure pattern** for consistency (logic, registration, index files)
8. **Use appropriate BaseErrorCode** values for different error types

Remember to keep this cheatsheet updated as the codebase evolves!
