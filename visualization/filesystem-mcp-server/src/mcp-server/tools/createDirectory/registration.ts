import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  CreateDirectoryInputSchema,
  createDirectoryLogic
} from './createDirectoryLogic.js';

/**
 * Registers the 'create_directory' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerCreateDirectoryTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterCreateDirectoryTool' });
  logger.info("Attempting to register 'create_directory' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'create_directory', // Tool name
        'Creates a directory. Optionally creates parent directories. Accepts relative or absolute paths.', // Description
        CreateDirectoryInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          // Validate input using the Zod schema
          const validationResult = CreateDirectoryInputSchema.safeParse(params);
          if (!validationResult.success) {
            const errorContext = requestContextService.createRequestContext({ operation: 'CreateDirectoryToolValidation' });
            logger.error('Invalid input parameters for create_directory tool', { ...errorContext, errors: validationResult.error.errors });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create context for this execution
          const callContext = requestContextService.createRequestContext({ operation: 'CreateDirectoryToolExecution' });
          logger.info(`Executing 'create_directory' tool for path: ${typedParams.path}, create_parents: ${typedParams.create_parents}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => createDirectoryLogic(typedParams, callContext),
            {
              operation: 'createDirectoryLogic',
              context: callContext,
              input: sanitization.sanitizeForLogging(typedParams), // Sanitize path
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'create_directory' for path: ${result.createdPath}, parentsCreated: ${result.parentsCreated}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'create_directory' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerCreateDirectoryTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
