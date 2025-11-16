import fs from 'fs/promises';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const DeleteDirectoryInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the directory to delete. Can be relative or absolute.'),
  recursive: z.boolean().default(false)
    .describe('If true, delete the directory and all its contents. If false, only delete if the directory is empty.'),
});

// Define the TypeScript type for the input
export type DeleteDirectoryInput = z.infer<typeof DeleteDirectoryInputSchema>;

// Define the TypeScript type for the output
export interface DeleteDirectoryOutput {
  message: string;
  deletedPath: string;
  wasRecursive: boolean;
}

/**
 * Deletes a specified directory, optionally recursively.
 *
 * @param {DeleteDirectoryInput} input - The input object containing path and recursive flag.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<DeleteDirectoryOutput>} A promise resolving with the deletion status.
 * @throws {McpError} For path errors, directory not found, not a directory, directory not empty (if not recursive), or I/O errors.
 */
export const deleteDirectoryLogic = async (input: DeleteDirectoryInput, context: RequestContext): Promise<DeleteDirectoryOutput> => {
  const { path: requestedPath, recursive } = input;
  const logicContext = { ...context, tool: 'deleteDirectoryLogic', recursive };
  logger.debug(`deleteDirectoryLogic: Received request to delete directory "${requestedPath}"`, logicContext);

  // Resolve the path
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`deleteDirectoryLogic: Resolved path to "${absolutePath}"`, { ...logicContext, requestedPath });

  try {
    // Check if the path exists and is a directory before attempting deletion
    let stats;
    try {
      stats = await fs.stat(absolutePath);
    } catch (statError: any) {
      if (statError.code === 'ENOENT') {
        logger.warning(`deleteDirectoryLogic: Directory not found at "${absolutePath}"`, { ...logicContext, requestedPath });
        throw new McpError(BaseErrorCode.NOT_FOUND, `Directory not found at path: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: statError });
      }
      throw statError; // Re-throw other stat errors
    }

    if (!stats.isDirectory()) {
      logger.warning(`deleteDirectoryLogic: Path is not a directory "${absolutePath}"`, { ...logicContext, requestedPath });
      throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Path is not a directory: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath });
    }

    // Attempt to delete the directory
    if (recursive) {
      // Use fs.rm for recursive deletion (available in Node.js 14.14.0+)
      await fs.rm(absolutePath, { recursive: true, force: true }); // force helps with potential permission issues on subfiles sometimes
      logger.info(`deleteDirectoryLogic: Successfully deleted directory recursively "${absolutePath}"`, { ...logicContext, requestedPath });
    } else {
      // Use fs.rmdir for non-recursive deletion (fails if not empty)
      await fs.rmdir(absolutePath);
      logger.info(`deleteDirectoryLogic: Successfully deleted empty directory "${absolutePath}"`, { ...logicContext, requestedPath });
    }

    return {
      message: `Successfully deleted directory: ${absolutePath}${recursive ? ' (recursively)' : ' (empty)'}`,
      deletedPath: absolutePath,
      wasRecursive: recursive,
    };

  } catch (error: any) {
    logger.error(`deleteDirectoryLogic: Error deleting directory "${absolutePath}"`, { ...logicContext, requestedPath, error: error.message, code: error.code });

    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }

    if (error.code === 'ENOENT') {
      // Should have been caught by stat, but handle defensively
      logger.warning(`deleteDirectoryLogic: Directory not found during delete operation "${absolutePath}"`, { ...logicContext, requestedPath });
      throw new McpError(BaseErrorCode.NOT_FOUND, `Directory not found at path: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
    }

    if (error.code === 'ENOTEMPTY' && !recursive) {
      logger.warning(`deleteDirectoryLogic: Directory not empty and recursive=false "${absolutePath}"`, { ...logicContext, requestedPath });
      throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Directory not empty: ${absolutePath}. Use recursive=true to delete non-empty directories.`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
    }

    // Handle other potential I/O errors (e.g., permissions)
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to delete directory: ${error.message || 'Unknown I/O error'}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
