import fs from 'fs/promises';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const DeleteFileInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the file to delete. Can be relative or absolute (resolved like readFile).'),
});

// Define the TypeScript type for the input
export type DeleteFileInput = z.infer<typeof DeleteFileInputSchema>;

// Define the TypeScript type for the output
export interface DeleteFileOutput {
  message: string;
  deletedPath: string;
}

/**
 * Deletes a specified file.
 *
 * @param {DeleteFileInput} input - The input object containing the path to the file.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<DeleteFileOutput>} A promise resolving with the deletion status.
 * @throws {McpError} For path errors, file not found, or I/O errors.
 */
export const deleteFileLogic = async (input: DeleteFileInput, context: RequestContext): Promise<DeleteFileOutput> => {
  const { path: requestedPath } = input;
  const logicContext = { ...context, tool: 'deleteFileLogic' };
  logger.debug(`deleteFileLogic: Received request to delete path "${requestedPath}"`, logicContext);

  // Resolve the path
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`deleteFileLogic: Resolved path to "${absolutePath}"`, { ...logicContext, requestedPath });

  try {
    // Check if the path exists and is a file before attempting deletion
    const stats = await fs.stat(absolutePath);
    if (!stats.isFile()) {
      logger.warning(`deleteFileLogic: Path is not a file "${absolutePath}"`, { ...logicContext, requestedPath });
      throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Path is not a file: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath });
    }

    // Attempt to delete the file
    await fs.unlink(absolutePath);
    logger.info(`deleteFileLogic: Successfully deleted file "${absolutePath}"`, { ...logicContext, requestedPath });

    return {
      message: `Successfully deleted file: ${absolutePath}`,
      deletedPath: absolutePath,
    };

  } catch (error: any) {
    logger.error(`deleteFileLogic: Error deleting file "${absolutePath}"`, { ...logicContext, requestedPath, error: error.message, code: error.code });

    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }

    if (error.code === 'ENOENT') {
      logger.warning(`deleteFileLogic: File not found at "${absolutePath}"`, { ...logicContext, requestedPath });
      // Even though we checked with stat, there's a small race condition possibility,
      // or the error came from stat itself. Treat ENOENT as file not found.
      throw new McpError(BaseErrorCode.NOT_FOUND, `File not found at path: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
    }

    // Handle other potential I/O errors
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to delete file: ${error.message || 'Unknown I/O error'}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
