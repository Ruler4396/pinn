import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  MovePathInputSchema,
  movePathLogic
} from './movePathLogic.js';

/**
 * Registers the 'move_path' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerMovePathTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterMovePathTool' });
  logger.info("Attempting to register 'move_path' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'move_path', // Tool name
        'Moves or renames a file or directory. Accepts relative or absolute paths for source and destination.', // Description
        MovePathInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = MovePathInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ operation: 'MovePathToolValidation' });
            logger.error('Invalid input parameters for move_path tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution
          const callContext = requestContextService.createRequestContext({ operation: 'MovePathToolExecution' });
          logger.info(`Executing 'move_path' tool from "${typedParams.source_path}" to "${typedParams.destination_path}"`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => movePathLogic(typedParams, callContext),
            {
              operation: 'movePathLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize paths
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'move_path' from "${result.sourcePath}" to "${result.destinationPath}"`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'move_path' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerMovePathTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
