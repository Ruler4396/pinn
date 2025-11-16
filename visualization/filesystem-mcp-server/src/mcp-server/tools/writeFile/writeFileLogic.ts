import fs from 'fs/promises';
import path from 'path';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js'; // Import serverState for path resolution

// Define the input schema using Zod for validation
export const WriteFileInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the file to write. Can be relative or absolute. If relative, it resolves against the path set by `set_filesystem_default`. If absolute, it is used directly. Missing directories will be created.'),
  content: z.string() // Allow empty content
    .describe('The content to write to the file. If the file exists, it will be overwritten.'),
});

// Define the TypeScript type for the input
export type WriteFileInput = z.infer<typeof WriteFileInputSchema>;

// Define the TypeScript type for the output (simple success message)
export interface WriteFileOutput {
  message: string;
  writtenPath: string;
  bytesWritten: number;
}

/**
 * Writes content to a specified file, overwriting it if it exists,
 * and creating necessary directories.
 *
 * @param {WriteFileInput} input - The input object containing the file path and content.
 * @param {RequestContext} context - The request context for logging and error handling.
 * @returns {Promise<WriteFileOutput>} A promise that resolves with a success message, the path written to, and bytes written.
 * @throws {McpError} Throws McpError for path resolution errors, I/O errors, or if the path resolves to a directory.
 */
export const writeFileLogic = async (input: WriteFileInput, context: RequestContext): Promise<WriteFileOutput> => {
  const { path: requestedPath, content } = input;
  logger.debug(`writeFileLogic: Received request for path "${requestedPath}"`, context);

  // Resolve the path using serverState (handles relative/absolute logic and sanitization)
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`writeFileLogic: Resolved path to "${absolutePath}"`, { ...context, requestedPath });

  try {
    // Ensure the target path is not a directory before attempting to write
    try {
      const stats = await fs.stat(absolutePath);
      if (stats.isDirectory()) {
        logger.warning(`writeFileLogic: Attempted to write to a directory path "${absolutePath}"`, { ...context, requestedPath });
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Cannot write file. Path exists and is a directory: ${absolutePath}`, { ...context, requestedPath, resolvedPath: absolutePath });
      }
    } catch (statError: any) {
      // ENOENT (file/dir doesn't exist) is expected and okay, we'll create it.
      // Other errors during stat (like permission issues) should be thrown.
      if (statError.code !== 'ENOENT') {
        throw statError; // Re-throw other stat errors
      }
      // If ENOENT, proceed to create directory and file
      logger.debug(`writeFileLogic: Path "${absolutePath}" does not exist, will create.`, { ...context, requestedPath });
    }

    // Ensure the directory exists before writing the file
    const dirName = path.dirname(absolutePath);
    logger.debug(`writeFileLogic: Ensuring directory "${dirName}" exists`, { ...context, requestedPath, resolvedPath: absolutePath });
    await fs.mkdir(dirName, { recursive: true });
    logger.debug(`writeFileLogic: Directory "${dirName}" confirmed/created`, { ...context, requestedPath, resolvedPath: absolutePath });

    // Write the file content
    logger.debug(`writeFileLogic: Writing content to "${absolutePath}"`, { ...context, requestedPath });
    await fs.writeFile(absolutePath, content, 'utf8');
    const bytesWritten = Buffer.byteLength(content, 'utf8');
    logger.info(`writeFileLogic: Successfully wrote ${bytesWritten} bytes to "${absolutePath}"`, { ...context, requestedPath });

    return {
      message: `Successfully wrote content to ${absolutePath}`,
      writtenPath: absolutePath,
      bytesWritten: bytesWritten,
    };
  } catch (error: any) {
     logger.error(`writeFileLogic: Error writing file to "${absolutePath}"`, { ...context, requestedPath, error: error.message, code: error.code });
    // Handle specific file system errors
    if (error instanceof McpError) {
        throw error; // Re-throw McpErrors (like the directory check)
    }
    // Handle potential I/O errors during mkdir or writeFile
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to write file: ${error.message || 'Unknown I/O error'}`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
