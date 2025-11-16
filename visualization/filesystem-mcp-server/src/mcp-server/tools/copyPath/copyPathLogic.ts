import fs from 'fs/promises';
import path from 'path';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const CopyPathInputSchema = z.object({
  source_path: z.string().min(1, 'Source path cannot be empty')
    .describe('The path of the file or directory to copy. Can be relative or absolute.'),
  destination_path: z.string().min(1, 'Destination path cannot be empty')
    .describe('The path where the copy should be created. Can be relative or absolute.'),
  recursive: z.boolean().default(true) // Defaulting to true as it's the common expectation for directory copies
    .describe('If copying a directory, whether to copy its contents recursively. Defaults to true.'),
});

// Define the TypeScript type for the input
export type CopyPathInput = z.infer<typeof CopyPathInputSchema>;

// Define the TypeScript type for the output
export interface CopyPathOutput {
  message: string;
  sourcePath: string;
  destinationPath: string;
  wasRecursive: boolean | null; // null if source was a file
}

/**
 * Copies a file or directory to a new location.
 *
 * @param {CopyPathInput} input - The input object containing source, destination, and recursive flag.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<CopyPathOutput>} A promise resolving with the copy status.
 * @throws {McpError} For path errors, source not found, destination already exists, or I/O errors.
 */
export const copyPathLogic = async (input: CopyPathInput, context: RequestContext): Promise<CopyPathOutput> => {
  const { source_path: requestedSourcePath, destination_path: requestedDestPath, recursive } = input;
  const logicContext = { ...context, tool: 'copyPathLogic', recursive };
  logger.debug(`copyPathLogic: Received request to copy "${requestedSourcePath}" to "${requestedDestPath}"`, logicContext);

  // Resolve source and destination paths
  const absoluteSourcePath = serverState.resolvePath(requestedSourcePath, context);
  const absoluteDestPath = serverState.resolvePath(requestedDestPath, context);
  logger.debug(`copyPathLogic: Resolved source to "${absoluteSourcePath}", destination to "${absoluteDestPath}"`, { ...logicContext, requestedSourcePath, requestedDestPath });

  // Basic check: source and destination cannot be the same
  if (absoluteSourcePath === absoluteDestPath) {
      logger.warning(`copyPathLogic: Source and destination paths are identical "${absoluteSourcePath}"`, logicContext);
      throw new McpError(BaseErrorCode.VALIDATION_ERROR, 'Source and destination paths cannot be the same.', { ...logicContext, absoluteSourcePath, absoluteDestPath });
  }

  try {
    // 1. Check if source exists and get its type (file or directory)
    let sourceStats;
    try {
      sourceStats = await fs.stat(absoluteSourcePath);
      logger.debug(`copyPathLogic: Source path "${absoluteSourcePath}" exists`, logicContext);
    } catch (statError: any) {
      if (statError.code === 'ENOENT') {
        logger.warning(`copyPathLogic: Source path not found "${absoluteSourcePath}"`, logicContext);
        throw new McpError(BaseErrorCode.NOT_FOUND, `Source path not found: ${absoluteSourcePath}`, { ...logicContext, requestedSourcePath, absoluteSourcePath, originalError: statError });
      }
      logger.error(`copyPathLogic: Cannot stat source path "${absoluteSourcePath}"`, { ...logicContext, error: statError.message });
      throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Cannot access source path: ${statError.message}`, { ...logicContext, requestedSourcePath, absoluteSourcePath, originalError: statError });
    }

    const isDirectory = sourceStats.isDirectory();
    const effectiveRecursive = isDirectory ? recursive : null; // Recursive flag only relevant for directories

    // 2. Check if destination *parent* directory exists
    const destDir = path.dirname(absoluteDestPath);
    try {
        await fs.access(destDir);
        logger.debug(`copyPathLogic: Destination parent directory "${destDir}" exists`, logicContext);
    } catch (parentAccessError: any) {
        logger.error(`copyPathLogic: Destination parent directory does not exist or is inaccessible "${destDir}"`, { ...logicContext, error: parentAccessError.message });
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Destination directory does not exist or is inaccessible: ${destDir}`, { ...logicContext, requestedDestPath, absoluteDestPath, destDir, originalError: parentAccessError });
    }

    // 3. Check if destination path already exists (fs.cp throws by default if destination exists)
     try {
        await fs.access(absoluteDestPath);
        // If access succeeds, the destination exists. Throw an error.
        logger.warning(`copyPathLogic: Destination path already exists "${absoluteDestPath}"`, logicContext);
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Destination path already exists: ${absoluteDestPath}. Cannot overwrite.`, { ...logicContext, requestedDestPath, absoluteDestPath });
    } catch (destAccessError: any) {
        if (destAccessError.code !== 'ENOENT') {
            // If error is something other than "Not Found", it's an unexpected issue.
            logger.error(`copyPathLogic: Error checking destination path "${absoluteDestPath}"`, { ...logicContext, error: destAccessError.message });
            throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Error checking destination path: ${destAccessError.message}`, { ...logicContext, requestedDestPath, absoluteDestPath, originalError: destAccessError });
        }
        // ENOENT means destination does not exist, which is good. Proceed.
        logger.debug(`copyPathLogic: Destination path "${absoluteDestPath}" does not exist, proceeding with copy`, logicContext);
    }

    // 4. Attempt to copy using fs.cp (Node.js v16.7.0+)
    // fs.cp handles both files and directories, respecting the recursive flag for directories.
    // It throws if the destination exists by default.
    await fs.cp(absoluteSourcePath, absoluteDestPath, {
        recursive: effectiveRecursive ?? false, // Pass recursive flag only if it's a directory
        errorOnExist: true, // Explicitly ensure it errors if destination exists (default behavior)
        force: false // Do not overwrite
    });

    logger.info(`copyPathLogic: Successfully copied "${absoluteSourcePath}" to "${absoluteDestPath}" (Recursive: ${effectiveRecursive})`, logicContext);

    return {
      message: `Successfully copied ${absoluteSourcePath} to ${absoluteDestPath}${isDirectory ? (recursive ? ' (recursively)' : ' (non-recursively, directory structure only)') : ''}`,
      sourcePath: absoluteSourcePath,
      destinationPath: absoluteDestPath,
      wasRecursive: effectiveRecursive,
    };

  } catch (error: any) {
    logger.error(`copyPathLogic: Error copying path "${absoluteSourcePath}" to "${absoluteDestPath}"`, { ...logicContext, error: error.message, code: error.code });

    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }

    // Handle potential I/O errors (e.g., permissions, disk full)
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to copy path: ${error.message || 'Unknown I/O error'}`, { ...logicContext, absoluteSourcePath, absoluteDestPath, originalError: error });
  }
};
