import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  DeleteDirectoryInputSchema,
  deleteDirectoryLogic
} from './deleteDirectoryLogic.js';

/**
 * Registers the 'delete_directory' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerDeleteDirectoryTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterDeleteDirectoryTool' });
  logger.info("Attempting to register 'delete_directory' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'delete_directory', // Tool name
        'Removes a directory. Optionally removes recursively. Accepts relative or absolute paths.', // Description
        DeleteDirectoryInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = DeleteDirectoryInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ operation: 'DeleteDirectoryToolValidation' });
            logger.error('Invalid input parameters for delete_directory tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution
          const callContext = requestContextService.createRequestContext({ operation: 'DeleteDirectoryToolExecution' });
          logger.info(`Executing 'delete_directory' tool for path: ${typedParams.path}, recursive: ${typedParams.recursive}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => deleteDirectoryLogic(typedParams, callContext),
            {
              operation: 'deleteDirectoryLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize path
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'delete_directory' for path: ${result.deletedPath}, recursive: ${result.wasRecursive}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'delete_directory' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerDeleteDirectoryTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
