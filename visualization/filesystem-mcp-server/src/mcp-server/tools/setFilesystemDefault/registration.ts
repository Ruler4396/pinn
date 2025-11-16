import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import {
  SetFilesystemDefaultInput,
  SetFilesystemDefaultInputSchema,
  setFilesystemDefaultLogic,
} from './setFilesystemDefaultLogic.js';

/**
 * Registers the 'set_filesystem_default' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerSetFilesystemDefaultTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterSetFilesystemDefaultTool' });
  logger.info("Attempting to register 'set_filesystem_default' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'set_filesystem_default', // Tool name
        'Sets a default absolute path for the current session. Relative paths used in other filesystem tools (like readFile) will be resolved against this default. The default is cleared on server restart.', // Description
        SetFilesystemDefaultInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          const typedParams = params as SetFilesystemDefaultInput;
          const callContext = requestContextService.createRequestContext({ operation: 'SetFilesystemDefaultToolExecution', parentId: registrationContext.requestId });
          logger.info(`Executing 'set_filesystem_default' tool with path: ${typedParams.path}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic (e.g., non-absolute path)
          const result = await ErrorHandler.tryCatch(
            () => setFilesystemDefaultLogic(typedParams, callContext),
            {
              operation: 'setFilesystemDefaultLogic',
              context: callContext,
              input: typedParams, // Input is automatically sanitized by ErrorHandler
              errorCode: BaseErrorCode.INTERNAL_ERROR // Default error if unexpected failure
            }
          );

          logger.info(`Successfully executed 'set_filesystem_default'. Current default: ${result.currentDefaultPath}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'set_filesystem_default' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerSetFilesystemDefaultTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
