import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  ListFilesInputSchema,
  listFilesLogic
} from './listFilesLogic.js';

/**
 * Registers the 'list_files' tool with the MCP server.
 * This tool lists files and directories at a specified path.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerListFilesTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterListFilesTool' });
  logger.info("Attempting to register 'list_files' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'list_files', // Tool name
        'Lists files and directories within the specified directory. Optionally lists recursively and returns a tree-like structure. Includes an optional `maxEntries` parameter (default 50) to limit the number of items returned.', // Updated Description
        ListFilesInputSchema.shape, // Pass the schema shape (already updated in logic file)
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = ListFilesInputSchema.safeParse(params);
          if (!validationResult.success) {
            // Create context without explicit parentRequestId
            const errorContext = requestContextService.createRequestContext({ operation: 'ListFilesToolValidation' });
            logger.error('Invalid input parameters for list_files tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution without explicit parentRequestId
          const callContext = requestContextService.createRequestContext({ operation: 'ListFilesToolExecution' });
          logger.info(`Executing 'list_files' tool for path: ${typedParams.path}, nested: ${typedParams.includeNested}`, callContext);

          // Call the logic function
          const result = await ErrorHandler.tryCatch(
            () => listFilesLogic(typedParams, callContext),
            {
              operation: 'listFilesLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize input for logging
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'list_files' for path: ${result.resolvedPath}. Items: ${result.itemCount}`, callContext);

          // Format the successful response - return the tree structure
          return {
            content: [{ type: 'text', text: result.tree }],
          };
        }
      );
      logger.info("'list_files' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerListFilesTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true // Critical for server startup
    }
  );
};
