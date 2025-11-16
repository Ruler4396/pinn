import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { ReadFileInput, ReadFileInputSchema, readFileLogic } from './readFileLogic.js';

/**
 * Registers the 'read_file' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerReadFileTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterReadFileTool' });
  logger.info("Attempting to register 'read_file' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      // Removed explicit generic <ReadFileInput>, let it be inferred from the schema
      server.tool(
        'read_file', // Tool name
        'Reads the entire content of a specified file as UTF-8 text. Accepts relative or absolute paths. Relative paths are resolved against the session default set by `set_filesystem_default`.', // Updated Description
        ReadFileInputSchema.shape, // Pass the schema shape, not the object instance
        async (params, extra) => { // Correct handler signature: params and extra
          // Cast params to the correct type within the handler for type safety
          const typedParams = params as ReadFileInput;
          // Create a new context for this specific tool execution
          // We might potentially use `extra.requestId` if available and needed for tracing, but let's keep it simple for now.
          const callContext = requestContextService.createRequestContext({ operation: 'ReadFileToolExecution', parentId: registrationContext.requestId });
          logger.info(`Executing 'read_file' tool for path: ${typedParams.path}`, callContext);

          // ErrorHandler will catch McpErrors thrown by readFileLogic and format them
          const result = await ErrorHandler.tryCatch(
            () => readFileLogic(typedParams, callContext), // Use typedParams
            {
              operation: 'readFileLogic',
              context: callContext,
              input: typedParams, // Input is automatically sanitized by ErrorHandler for logging
              errorCode: BaseErrorCode.INTERNAL_ERROR // Default error if unexpected failure
            }
          );

          logger.info(`Successfully read file: ${typedParams.path}`, callContext); // Use typedParams

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.content }],
          };
        }
      );
      logger.info("'read_file' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerReadFileTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR, // Error code if registration itself fails
      critical: true // Failure to register is critical
    }
  );
};
