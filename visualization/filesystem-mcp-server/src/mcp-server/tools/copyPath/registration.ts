import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  CopyPathInputSchema,
  copyPathLogic
} from './copyPathLogic.js';

/**
 * Registers the 'copy_path' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerCopyPathTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterCopyPathTool' });
  logger.info("Attempting to register 'copy_path' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'copy_path', // Tool name
        'Copies a file or directory to a new location. Accepts relative or absolute paths. Defaults to recursive copy for directories.', // Description
        CopyPathInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = CopyPathInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ operation: 'CopyPathToolValidation' });
            logger.error('Invalid input parameters for copy_path tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution
          const callContext = requestContextService.createRequestContext({ operation: 'CopyPathToolExecution' });
          logger.info(`Executing 'copy_path' tool from "${typedParams.source_path}" to "${typedParams.destination_path}", recursive: ${typedParams.recursive}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => copyPathLogic(typedParams, callContext),
            {
              operation: 'copyPathLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize paths
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'copy_path' from "${result.sourcePath}" to "${result.destinationPath}", recursive: ${result.wasRecursive}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'copy_path' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerCopyPathTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
