import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  DeleteFileInputSchema,
  deleteFileLogic
} from './deleteFileLogic.js';

/**
 * Registers the 'delete_file' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerDeleteFileTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterDeleteFileTool' });
  logger.info("Attempting to register 'delete_file' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'delete_file', // Tool name
        'Removes a specific file. Accepts relative or absolute paths.', // Description
        DeleteFileInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = DeleteFileInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ operation: 'DeleteFileToolValidation' });
            logger.error('Invalid input parameters for delete_file tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution
          const callContext = requestContextService.createRequestContext({ operation: 'DeleteFileToolExecution' });
          logger.info(`Executing 'delete_file' tool for path: ${typedParams.path}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => deleteFileLogic(typedParams, callContext),
            {
              operation: 'deleteFileLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize path if needed
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'delete_file' for path: ${result.deletedPath}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'delete_file' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerDeleteFileTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
