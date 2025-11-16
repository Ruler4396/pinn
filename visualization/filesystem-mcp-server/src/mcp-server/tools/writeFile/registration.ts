import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { ErrorHandler } from '../../../utils/internal/errorHandler.js';
import { logger } from '../../../utils/internal/logger.js';
import { requestContextService } from '../../../utils/internal/requestContext.js';
import {
  WriteFileInput,
  WriteFileInputSchema,
  writeFileLogic,
} from './writeFileLogic.js';

/**
 * Registers the 'write_file' tool with the MCP server.
 *
 * @param {McpServer} server - The McpServer instance to register the tool with.
 * @returns {Promise<void>} A promise that resolves when the tool is registered.
 * @throws {McpError} Throws an error if registration fails.
 */
export const registerWriteFileTool = async (server: McpServer): Promise<void> => {
  const registrationContext = requestContextService.createRequestContext({ operation: 'RegisterWriteFileTool' });
  logger.info("Attempting to register 'write_file' tool", registrationContext);

  await ErrorHandler.tryCatch(
    async () => {
      server.tool(
        'write_file', // Tool name
        'Writes content to a specified file. Creates the file (and necessary directories) if it doesn\'t exist, or overwrites it if it does. Accepts relative or absolute paths (resolved like readFile).', // Description
        WriteFileInputSchema.shape, // Pass the schema shape
        async (params, extra) => {
          const typedParams = params as WriteFileInput;
          const callContext = requestContextService.createRequestContext({ operation: 'WriteFileToolExecution', parentId: registrationContext.requestId });
          logger.info(`Executing 'write_file' tool for path: ${typedParams.path}`, callContext);

          // ErrorHandler will catch McpErrors thrown by the logic
          const result = await ErrorHandler.tryCatch(
            () => writeFileLogic(typedParams, callContext),
            {
              operation: 'writeFileLogic',
              context: callContext,
              input: { path: typedParams.path, content: '[CONTENT REDACTED]' }, // Redact content for logging
              errorCode: BaseErrorCode.INTERNAL_ERROR
            }
          );

          logger.info(`Successfully executed 'write_file' for path: ${result.writtenPath}`, callContext);

          // Format the successful response
          return {
            content: [{ type: 'text', text: result.message }],
          };
        }
      );
      logger.info("'write_file' tool registered successfully", registrationContext);
    },
    {
      operation: 'registerWriteFileTool',
      context: registrationContext,
      errorCode: BaseErrorCode.CONFIGURATION_ERROR,
      critical: true
    }
  );
};
