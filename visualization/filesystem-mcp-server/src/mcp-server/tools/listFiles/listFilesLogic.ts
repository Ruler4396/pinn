import fs from 'fs/promises';
import path from 'path';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the input schema using Zod for validation
export const ListFilesInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the directory to list. Can be relative or absolute (resolved like readFile).'),
  includeNested: z.boolean().default(false)
    .describe('If true, list files and directories recursively. Defaults to false (top-level only).'),
  maxEntries: z.number().int().positive().optional().default(50) // Updated default to 50
    .describe('Maximum number of directory entries (files + folders) to return. Defaults to 50. Helps prevent excessive output for large directories.'),
});

// Define the TypeScript type for the input
export type ListFilesInput = z.infer<typeof ListFilesInputSchema>;

// Define the TypeScript type for the output
export interface ListFilesOutput {
  message: string;
  tree: string;
  requestedPath: string;
  resolvedPath: string;
  itemCount: number;
  truncated: boolean; // Added flag
}

interface DirectoryItem {
  name: string;
  isDirectory: boolean;
  children?: DirectoryItem[]; // Only populated if includeNested is true
  error?: string; // Added to indicate read errors for this directory
}

/**
 * Recursively reads directory contents and builds a tree structure.
 *
 * @param {string} dirPath - The absolute path to the directory.
 * @param {boolean} includeNested - Whether to recurse into subdirectories.
 * @param {RequestContext} context - The request context for logging.
 * @param {{ count: number, limit: number, truncated: boolean }} state - Mutable state to track count and limit across recursive calls.
 * @returns {Promise<DirectoryItem[]>} A promise resolving with the list of items.
 * @throws {McpError} If reading the directory fails.
 */
const readDirectoryRecursive = async (
  dirPath: string,
  includeNested: boolean,
  context: RequestContext,
  state: { count: number; limit: number; truncated: boolean } // Pass state object
): Promise<DirectoryItem[]> => {
  if (state.truncated || state.count >= state.limit) {
    state.truncated = true; // Ensure truncated flag is set if limit reached before starting
    return []; // Stop processing if limit already reached
  }

  const items: DirectoryItem[] = [];
  let entries;
  try {
    entries = await fs.readdir(dirPath, { withFileTypes: true });
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      logger.warning(`Directory not found: ${dirPath}`, context);
      throw new McpError(BaseErrorCode.NOT_FOUND, `Directory not found at path: ${dirPath}`, { ...context, dirPath, originalError: error });
    } else if (error.code === 'ENOTDIR') {
       logger.warning(`Path is not a directory: ${dirPath}`, context);
       throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Path is not a directory: ${dirPath}`, { ...context, dirPath, originalError: error });
    }
    logger.error(`Failed to read directory: ${dirPath}`, { ...context, error: error.message });
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to read directory: ${error.message}`, { ...context, dirPath, originalError: error });
  }

  for (const entry of entries) {
    if (state.count >= state.limit) {
      state.truncated = true;
      logger.debug(`Max entries limit (${state.limit}) reached while processing ${dirPath}`, context);
      break; // Stop processing entries in this directory
    }

    state.count++; // Increment count for this entry

    const itemPath = path.join(dirPath, entry.name);
    const item: DirectoryItem = {
      name: entry.name,
      isDirectory: entry.isDirectory(),
    };

    if (item.isDirectory && includeNested) {
      // Recursively read subdirectory, passing the shared state object
      try {
        // Pass the same state object down
        item.children = await readDirectoryRecursive(itemPath, includeNested, { ...context, parentPath: dirPath }, state);
      } catch (recursiveError) {
         // Log the error from the recursive call but continue processing other entries
         logger.error(`Error reading nested directory ${itemPath}`, { ...context, error: (recursiveError as Error).message, code: (recursiveError as McpError).code });
         // Log the error and mark the item
         const errorMessage = (recursiveError as McpError)?.message || (recursiveError as Error)?.message || 'Unknown error reading directory';
         logger.error(`Error reading nested directory ${itemPath}`, { ...context, error: errorMessage, code: (recursiveError as McpError)?.code });
         item.error = errorMessage; // Store the error message on the item
         item.children = undefined; // Ensure no children are processed or displayed for errored directories
      }
    }
    items.push(item);

    // Check limit again after potentially adding children (though count is incremented per item)
    if (state.truncated) {
       break; // Exit loop if limit was hit during recursive call
    }
  }

  // Sort items: directories first, then files, alphabetically
  items.sort((a, b) => {
    if (a.isDirectory !== b.isDirectory) {
      return a.isDirectory ? -1 : 1; // Directories first
    }
    return a.name.localeCompare(b.name); // Then sort alphabetically
  });

  return items;
};

/**
 * Formats the directory items into a tree-like string.
 *
 * @param {DirectoryItem[]} items - The items to format.
 * @param {string} prefix - The prefix string for indentation.
 * @param {boolean} truncated - Whether the listing was cut short due to limits.
 * @returns {string} The formatted tree string.
 */
const formatTree = (items: DirectoryItem[], truncated: boolean, prefix = ''): string => {
  let treeString = '';
  items.forEach((item, index) => {
    const isLast = index === items.length - 1;
    const connector = isLast ? '└── ' : '├── ';
    const itemPrefix = item.isDirectory ? '📁 ' : '📄 ';
    const errorMarker = item.error ? ` [Error: ${item.error}]` : ''; // Add error marker if present
    treeString += `${prefix}${connector}${itemPrefix}${item.name}${errorMarker}\n`;

    // Only recurse if it's a directory, has children defined (not errored), and children exist
    if (item.isDirectory && !item.error && item.children && item.children.length > 0) {
      const childPrefix = prefix + (isLast ? '    ' : '│   ');
      // Pass truncated flag down, but don't add the message recursively
      treeString += formatTree(item.children, false, childPrefix);
    } else if (item.isDirectory && item.error) {
      // Optionally add a specific marker for children of errored directories,
      // but the error on the parent line is likely sufficient.
    }
  });

  // Add truncation message at the end of the current level if needed
  if (truncated && prefix === '') { // Only add at the top level formatting call
      treeString += `${prefix}...\n${prefix}[Listing truncated due to max entries limit]\n`;
  }

  return treeString;
};

/**
 * Lists files and directories at a given path, optionally recursively.
 *
 * @param {ListFilesInput} input - The input object containing path and options.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<ListFilesOutput>} A promise resolving with the listing results.
 * @throws {McpError} For path errors, directory not found, or I/O errors.
 */
export const listFilesLogic = async (input: ListFilesInput, context: RequestContext): Promise<ListFilesOutput> => {
  // Destructure validated input, including the new maxEntries
  const { path: requestedPath, includeNested, maxEntries } = input;
  const logicContext = { ...context, includeNested, maxEntries };
  logger.debug(`listFilesLogic: Received request for path "${requestedPath}" with limit ${maxEntries}`, logicContext);

  // Resolve the path
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`listFilesLogic: Resolved path to "${absolutePath}"`, { ...logicContext, requestedPath });

  try {
    // Initialize state for tracking count and limit, using the potentially updated default
    const state = { count: 0, limit: maxEntries, truncated: false };

    // Read directory structure using the state object
    const items = await readDirectoryRecursive(absolutePath, includeNested, logicContext, state);

    // Format the tree, passing the final truncated state
    const rootName = path.basename(absolutePath);
    const tree = `📁 ${rootName}\n` + formatTree(items, state.truncated); // Pass truncated flag

    const message = state.truncated
      ? `Successfully listed ${state.count} items in ${absolutePath} (truncated at limit of ${maxEntries}).` // Use maxEntries from input for message
      : `Successfully listed ${state.count} items in ${absolutePath}.`;

    logger.info(`listFilesLogic: ${message}`, { ...logicContext, requestedPath, itemCount: state.count, truncated: state.truncated, limit: maxEntries });

    return {
      message: message,
      tree: tree,
      requestedPath: requestedPath,
      resolvedPath: absolutePath,
      itemCount: state.count, // Return the actual count processed
      truncated: state.truncated,
    };

  } catch (error: any) {
    // Errors during readDirectoryRecursive are already logged and potentially thrown as McpError
    logger.error(`listFilesLogic: Error listing files at "${absolutePath}"`, { ...logicContext, requestedPath, error: error.message, code: error.code });
    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }
    // Catch any other unexpected errors
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to list files: ${error.message || 'Unknown I/O error'}`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
