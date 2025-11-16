import fs from 'fs/promises'; // Ensure fs is imported
import { z } from 'zod';
// No longer need config for base directory here
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js'; // Import serverState for path resolution
// No longer need sanitization directly here for path resolution

// Define the input schema using Zod for validation - Updated description
export const ReadFileInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the file to read. Can be relative or absolute. If relative, it resolves against the path set by `set_filesystem_default`. If absolute, it is used directly. If relative and no default is set, an error occurs.'),
});

// Define the TypeScript type for the input
export type ReadFileInput = z.infer<typeof ReadFileInputSchema>;

// Define the TypeScript type for the output
export interface ReadFileOutput {
  content: string;
}

/**
 * Reads the content of a specified file.
 *
 * @param {ReadFileInput} input - The input object containing the file path.
 * @param {RequestContext} context - The request context for logging and error handling.
 * @returns {Promise<ReadFileOutput>} A promise that resolves with the file content.
 * @throws {McpError} Throws McpError for path resolution errors, file not found, or I/O errors.
 */
export const readFileLogic = async (input: ReadFileInput, context: RequestContext): Promise<ReadFileOutput> => {
  const { path: requestedPath } = input;

  // Resolve the path using serverState (handles relative/absolute logic and sanitization)
  // This will throw McpError if a relative path is given without a default set.
  const absolutePath = serverState.resolvePath(requestedPath, context);

  try {
    // Read the file content using the resolved absolute path
    const content = await fs.readFile(absolutePath, 'utf8');
    return { content };
  } catch (error: any) {
    // Handle specific file system errors
    // Handle specific file system errors using the resolved absolutePath in messages
    if (error.code === 'ENOENT') {
      // Use NOT_FOUND error code
      throw new McpError(BaseErrorCode.NOT_FOUND, `File not found at resolved path: ${absolutePath}`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: error });
    }
    if (error.code === 'EISDIR') {
       // Use VALIDATION_ERROR
       throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Resolved path is a directory, not a file: ${absolutePath}`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: error });
    }
    // Handle other potential I/O errors using INTERNAL_ERROR
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to read file: ${error.message || 'Unknown I/O error'}`, { ...context, originalError: error });
  }
};
