import fs from 'fs/promises';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const CreateDirectoryInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the directory to create. Can be relative or absolute.'),
  create_parents: z.boolean().default(true)
    .describe('If true, create any necessary parent directories that don\'t exist. If false, fail if a parent directory is missing.'),
});

// Define the TypeScript type for the input
export type CreateDirectoryInput = z.infer<typeof CreateDirectoryInputSchema>;

// Define the TypeScript type for the output
export interface CreateDirectoryOutput {
  message: string;
  createdPath: string;
  parentsCreated: boolean; // Indicate if parent directories were also created
}

/**
 * Creates a specified directory, optionally creating parent directories.
 *
 * @param {CreateDirectoryInput} input - The input object containing path and create_parents flag.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<CreateDirectoryOutput>} A promise resolving with the creation status.
 * @throws {McpError} For path errors, if the path already exists and is not a directory, or I/O errors.
 */
export const createDirectoryLogic = async (input: CreateDirectoryInput, context: RequestContext): Promise<CreateDirectoryOutput> => {
  const { path: requestedPath, create_parents } = input;
  const logicContext = { ...context, tool: 'createDirectoryLogic', create_parents };
  logger.debug(`createDirectoryLogic: Received request to create directory "${requestedPath}"`, logicContext);

  // Resolve the path
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`createDirectoryLogic: Resolved path to "${absolutePath}"`, { ...logicContext, requestedPath });

  try {
    // Check if path already exists
    try {
      const stats = await fs.stat(absolutePath);
      if (stats.isDirectory()) {
        logger.info(`createDirectoryLogic: Directory already exists at "${absolutePath}"`, { ...logicContext, requestedPath });
        // Directory already exists, consider this a success (idempotent)
        return {
          message: `Directory already exists: ${absolutePath}`,
          createdPath: absolutePath,
          parentsCreated: false, // No parents needed to be created now
        };
      } else {
        // Path exists but is not a directory (e.g., a file)
        logger.error(`createDirectoryLogic: Path exists but is not a directory "${absolutePath}"`, { ...logicContext, requestedPath });
        throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Path already exists but is not a directory: ${absolutePath}`, { ...logicContext, requestedPath, resolvedPath: absolutePath });
      }
    } catch (statError: any) {
      if (statError.code !== 'ENOENT') {
        // If error is something other than "Not Found", re-throw it
        throw statError;
      }
      // Path does not exist, proceed with creation
      logger.debug(`createDirectoryLogic: Path does not exist, proceeding with creation "${absolutePath}"`, { ...logicContext, requestedPath });
    }

    // Attempt to create the directory
    await fs.mkdir(absolutePath, { recursive: create_parents });
    logger.info(`createDirectoryLogic: Successfully created directory "${absolutePath}" (parents: ${create_parents})`, { ...logicContext, requestedPath });

    return {
      message: `Successfully created directory: ${absolutePath}${create_parents ? ' (including parents if needed)' : ''}`,
      createdPath: absolutePath,
      parentsCreated: create_parents, // Reflects the *option* enabled, not necessarily if they *were* created
    };

  } catch (error: any) {
    logger.error(`createDirectoryLogic: Error creating directory "${absolutePath}"`, { ...logicContext, requestedPath, error: error.message, code: error.code });

    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }

    // Handle potential I/O errors (e.g., permissions, invalid path components)
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to create directory: ${error.message || 'Unknown I/O error'}`, { ...logicContext, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
