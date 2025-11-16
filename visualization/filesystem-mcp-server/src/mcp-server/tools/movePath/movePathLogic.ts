import fs from 'fs/promises';
import path from 'path';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const MovePathInputSchema = z.object({
  source_path: z.string().min(1, 'Source path cannot be empty')
    .describe('The current path of the file or directory to move. Can be relative or absolute.'),
  destination_path: z.string().min(1, 'Destination path cannot be empty')
    .describe('The new path for the file or directory. Can be relative or absolute.'),
});

// Define the TypeScript type for the input
export type MovePathInput = z.infer<typeof MovePathInputSchema>;

// Define the TypeScript type for the output
export interface MovePathOutput {
  message: string;
  sourcePath: string;
  destinationPath: string;
}

/**
 * Moves or renames a file or directory.
 *
 * @param {MovePathInput} input - The input object containing source and destination paths.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<MovePathOutput>} A promise resolving with the move status.
 * @throws {McpError} For path errors, source not found, destination already exists (depending on OS/FS behavior), or I/O errors.
 */
export const movePathLogic = async (input: MovePathInput, context: RequestContext): Promise<MovePathOutput> => {
  const { source_path: requestedSourcePath, destination_path: requestedDestPath } = input;
  const logicContext = { ...context, tool: 'movePathLogic' };
  logger.debug(`movePathLogic: Received request to move "${requestedSourcePath}" to "${requestedDestPath}"`, logicContext);

  // Resolve source and destination paths
  const absoluteSourcePath = serverState.resolvePath(requestedSourcePath, context);
  const absoluteDestPath = serverState.resolvePath(requestedDestPath, context);
  logger.debug(`movePathLogic: Resolved source to "${absoluteSourcePath}", destination to "${absoluteDestPath}"`, { ...logicContext, requestedSourcePath, requestedDestPath });

  // Basic check: source and destination cannot be the same
  if (absoluteSourcePath === absoluteDestPath) {
      logger.warning(`movePathLogic: Source and destination paths are identical "${absoluteSourcePath}"`, logicContext);
      throw new McpError(BaseErrorCode.VALIDATION_ERROR, 'Source and destination paths cannot be the same.', { ...logicContext, absoluteSourcePath, absoluteDestPath });
  }

  try {
    // 1. Check if source exists
    try {
      await fs.access(absoluteSourcePath); // Check existence and permissions
      logger.debug(`movePathLogic: Source path "${absoluteSourcePath}" exists and is accessible`, logicContext);
    } catch (accessError: any) {
      if (accessError.code === 'ENOENT') {
        logger.warning(`movePathLogic: Source path not found "${absoluteSourcePath}"`, logicContext);
        throw new McpError(BaseErrorCode.NOT_FOUND, `Source path not found: ${absoluteSourcePath}`, { ...logicContext, requestedSourcePath, absoluteSourcePath, originalError: accessError });
      }
      // Other access errors (e.g., permissions)
      logger.error(`movePathLogic: Cannot access source path "${absoluteSourcePath}"`, { ...logicContext, error: accessError.message });
      throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Cannot access source path: ${accessError.message}`, { ...logicContext, requestedSourcePath, absoluteSourcePath, originalError: accessError });
    }

    // 2. Check if destination *parent* directory exists
    const destDir = path.dirname(absoluteDestPath);
    try {
        await fs.access(destDir);
        logger.debug(`movePathLogic: Destination parent directory "${destDir}" exists`, logicContext);
    } catch (parentAccessError: any) {
        logger.error(`movePathLogic: Destination parent directory does not exist or is inaccessible "${destDir}"`, { ...logicContext, error: parentAccessError.message });
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Destination directory does not exist or is inaccessible: ${destDir}`, { ...logicContext, requestedDestPath, absoluteDestPath, destDir, originalError: parentAccessError });
    }

    // 3. Check if destination path already exists (fs.rename behavior varies, so check explicitly)
    try {
        await fs.access(absoluteDestPath);
        // If access succeeds, the destination exists. Throw an error.
        logger.warning(`movePathLogic: Destination path already exists "${absoluteDestPath}"`, logicContext);
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Destination path already exists: ${absoluteDestPath}. Cannot overwrite.`, { ...logicContext, requestedDestPath, absoluteDestPath });
    } catch (destAccessError: any) {
        if (destAccessError.code !== 'ENOENT') {
            // If error is something other than "Not Found", it's an unexpected issue.
            logger.error(`movePathLogic: Error checking destination path "${absoluteDestPath}"`, { ...logicContext, error: destAccessError.message });
            throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Error checking destination path: ${destAccessError.message}`, { ...logicContext, requestedDestPath, absoluteDestPath, originalError: destAccessError });
        }
        // ENOENT means destination does not exist, which is good. Proceed.
        logger.debug(`movePathLogic: Destination path "${absoluteDestPath}" does not exist, proceeding with move`, logicContext);
    }


    // 4. Attempt to move/rename
    await fs.rename(absoluteSourcePath, absoluteDestPath);
    logger.info(`movePathLogic: Successfully moved "${absoluteSourcePath}" to "${absoluteDestPath}"`, logicContext);

    return {
      message: `Successfully moved ${absoluteSourcePath} to ${absoluteDestPath}`,
      sourcePath: absoluteSourcePath,
      destinationPath: absoluteDestPath,
    };

  } catch (error: any) {
    logger.error(`movePathLogic: Error moving path "${absoluteSourcePath}" to "${absoluteDestPath}"`, { ...logicContext, error: error.message, code: error.code });

    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors (like source not found, dest exists)
    }

    // Handle other potential I/O errors (e.g., permissions, cross-device link)
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to move path: ${error.message || 'Unknown I/O error'}`, { ...logicContext, absoluteSourcePath, absoluteDestPath, originalError: error });
  }
};
