import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import { sanitization } from '../../../utils/security/sanitization.js';
import {
  UpdateFileInputSchema,
  updateFileLogic
} from './updateFileLogic.js';

/**
 * Registers the 'update_file' tool with the MCP server.
 * This tool accepts a JSON object with 'path', 'blocks' (array of {search, replace}),
 * and optional 'useRegex' and 'replaceAll' flags.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerUpdateFileTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterUpdateFileTool' });
  logger.info("Attempting to register 'update_file' tool with JSON input format", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'update_file', // Tool name
        'Performs targeted search-and-replace operations within an existing file using an array of {search, replace} blocks. Preferred for smaller, localized changes. For large-scale updates or overwrites, consider using `write_file`. Accepts relative or absolute paths. File must exist. Supports optional `useRegex` (boolean, default false) and `replaceAll` (boolean, default false).', // Emphasized usage guidance
        UpdateFileInputSchema.shape, // Pass the updated schema shape
        async (params, extra) => {
          // Validate input using the Zod schema before proceeding
          const validationResult = UpdateFileInputSchema.safeParse(params);
          if (!validationResult.success) {
            // Create a new context for validation error
            const errorContext = requestContextService.createRequestContext({ operation: 'UpdateFileToolValidation' });
            logger.error('Invalid input parameters for update_file tool', { ...errorContext, errors: validationResult.error.errors });
            // Throw McpError for invalid parameters
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid parameters: ${validationResult.error.errors.map(e => `${e.path.join('.')} - ${e.message}`).join(', ')}`, errorContext);
          }
          const typedParams = validationResult.data; // Use validated data

          // Create a new context for this specific tool execution
          const callContext = requestContextService.createRequestContext({ operation: 'UpdateFileToolExecution' });
          logger.info(`Executing 'update_file' tool for path: ${typedParams.path} with ${typedParams.blocks.length} blocks`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => updateFileLogic(typedParams, callContext),
            {
              operation: 'updateFileLogic',
              context: callContext,
              // Sanitize input for logging: keep path, redact block content
              input: sanitization.sanitizeForLogging({
                  path: typedParams.path,
                  blocks: typedParams.blocks.map((_, index) => `[Block ${index + 1} REDACTED]`), // Redact block details
                  useRegex: typedParams.useRegex,
                  replaceAll: typedParams.replaceAll,
              }),
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'update_file' for path: ${result.updatedPath}. Blocks Applied: ${result.blocksApplied}, Failed: ${result.blocksFailed}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'update_file' tool registered successfully with JSON input format", registrationContext);
    },
    {
      operation: 'registerUpdateFileTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
