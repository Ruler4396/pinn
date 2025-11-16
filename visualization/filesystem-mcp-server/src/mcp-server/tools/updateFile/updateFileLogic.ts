import fs from 'fs/promises';
import { z } from 'zod';
import { BaseErrorCode, McpError } from '../../../types-global/errors.js';
import { logger } from '../../../utils/internal/logger.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js';

// Define the structure for a single search/replace block
const DiffBlockSchema = z.object({
  search: z.string().min(1, 'Search pattern cannot be empty'),
  replace: z.string(), // Allow empty replace string for deletions
});

// Define the input schema using Zod for validation
export const UpdateFileInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The path to the file to update. Can be relative or absolute (resolved like readFile). The file must exist.'),
  blocks: z.array(DiffBlockSchema).min(1, 'At least one search/replace block is required.')
    .describe('An array of objects, each with a `search` (string) and `replace` (string) property.'),
  useRegex: z.boolean().default(false)
    .describe('If true, treat the `search` field of each block as a JavaScript regular expression pattern. Defaults to false (exact string matching).'),
  replaceAll: z.boolean().default(false)
    .describe('If true, replace all occurrences matching the SEARCH criteria within the file. If false, only replace the first occurrence. Defaults to false.'),
});

// Define the TypeScript type for the input
export type UpdateFileInput = z.infer<typeof UpdateFileInputSchema>;

// Define the TypeScript type for a single block based on the schema, adding internal tracking
export type DiffBlock = z.infer<typeof DiffBlockSchema> & { applied?: boolean };

// Define the TypeScript type for the output
export interface UpdateFileOutput {
  message: string;
  updatedPath: string;
  blocksApplied: number;
  blocksFailed: number; // Track blocks that didn't find a match
}

/**
 * Applies an array of search/replace blocks sequentially to the file content.
 *
 * @param {UpdateFileInput} input - The input object containing path, blocks, and options.
 * @param {RequestContext} context - The request context.
 * @returns {Promise<UpdateFileOutput>} A promise resolving with update status.
 * @throws {McpError} For path errors, file not found, I/O errors, or invalid regex patterns.
 */
export const updateFileLogic = async (input: UpdateFileInput, context: RequestContext): Promise<UpdateFileOutput> => {
  // Destructure validated input
  const { path: requestedPath, blocks: inputBlocks, useRegex, replaceAll } = input;
  const logicContext = { ...context, useRegex, replaceAll };
  logger.debug(`updateFileLogic: Received request for path "${requestedPath}" with ${inputBlocks.length} blocks`, logicContext);

  // Resolve the path
  const absolutePath = serverState.resolvePath(requestedPath, context);
  logger.debug(`updateFileLogic: Resolved path to "${absolutePath}"`, { ...context, requestedPath });

  try {
    // 1. Read the existing file content
    let currentContent: string;
    try {
      currentContent = await fs.readFile(absolutePath, 'utf8');
      logger.debug(`updateFileLogic: Successfully read existing file "${absolutePath}"`, { ...context, requestedPath });
    } catch (readError: any) {
      if (readError.code === 'ENOENT') {
        logger.warning(`updateFileLogic: File not found at "${absolutePath}"`, { ...context, requestedPath });
        throw new McpError(BaseErrorCode.NOT_FOUND, `File not found at path: ${absolutePath}. Cannot update a non-existent file.`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: readError });
      }
      throw readError; // Re-throw other read errors
    }

    // 2. Input blocks are already parsed and validated by Zod
    const diffBlocks: DiffBlock[] = inputBlocks.map(block => ({ ...block, applied: false })); // Add internal 'applied' flag

    // 3. Apply blocks sequentially
    let updatedContent = currentContent;
    let blocksApplied = 0;
    let blocksFailed = 0;
    let totalReplacementsMade = 0; // Track individual replacements if replaceAll is true

    for (let i = 0; i < diffBlocks.length; i++) {
      const block = diffBlocks[i];
      // Create context specific to this block's processing
      const blockContext = { ...logicContext, blockIndex: i, searchPreview: block.search.substring(0, 50) };
      let blockMadeChange = false;
      let replacementsInBlock = 0; // Count replacements made by *this specific block*

      try {
        if (useRegex) {
          // Treat search as regex pattern
          // Create the regex. Add 'g' flag if replaceAll is true.
          const regex = new RegExp(block.search, replaceAll ? 'g' : '');
          const matches = updatedContent.match(regex); // Find matches before replacing

          if (matches && matches.length > 0) {
             updatedContent = updatedContent.replace(regex, block.replace);
             replacementsInBlock = matches.length; // Count actual matches found
             blockMadeChange = true;
             logger.debug(`Applied regex block`, blockContext);
          }
        } else {
          // Treat search as exact string
          if (replaceAll) {
            let startIndex = 0;
            let index;
            let replaced = false;
            // Use split/join for robust replacement of all occurrences
            const parts = updatedContent.split(block.search);
            if (parts.length > 1) { // Check if the search string was found at all
                updatedContent = parts.join(block.replace);
                replacementsInBlock = parts.length - 1; // Number of replacements is one less than the number of parts
                replaced = true;
            }

            if (replaced) {
               blockMadeChange = true;
               logger.debug(`Applied string block (replaceAll=true)`, blockContext);
            }
          } else {
            // Replace only the first occurrence
            const index = updatedContent.indexOf(block.search);
            if (index !== -1) {
              updatedContent = updatedContent.substring(0, index) + block.replace + updatedContent.substring(index + block.search.length);
              replacementsInBlock = 1;
              blockMadeChange = true;
              logger.debug(`Applied string block (replaceAll=false)`, blockContext);
            }
          }
        }
      } catch (regexError: any) {
         if (regexError instanceof SyntaxError && useRegex) {
            logger.error('Invalid regex pattern provided in SEARCH block', { ...blockContext, error: regexError.message });
            throw new McpError(BaseErrorCode.VALIDATION_ERROR, `Invalid regular expression pattern in block ${i + 1}: "${block.search}". Error: ${regexError.message}`, blockContext);
         }
         // Re-throw other unexpected errors during replacement
         logger.error('Unexpected error during replacement operation', { ...blockContext, error: regexError.message });
         throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Error processing block ${i + 1}: ${regexError.message}`, blockContext);
      }


      if (blockMadeChange) {
        block.applied = true; // Mark the block as having made a change
        blocksApplied++;
        totalReplacementsMade += replacementsInBlock; // Add replacements from this block to total
      } else {
        blocksFailed++;
        logger.warning(`Diff block search criteria not found`, blockContext);
      }
    }

    // 4. Write the updated content back to the file only if changes were actually made
    if (totalReplacementsMade > 0) { // Check if any replacement occurred across all blocks
      logger.debug(`updateFileLogic: Writing updated content back to "${absolutePath}"`, logicContext);
      await fs.writeFile(absolutePath, updatedContent, 'utf8');
      logger.info(`updateFileLogic: Successfully updated file "${absolutePath}"`, { ...logicContext, requestedPath, blocksApplied, blocksFailed, totalReplacementsMade });
      const replaceMsg = `Made ${totalReplacementsMade} replacement(s) across ${blocksApplied} block(s).`;
      return {
        message: `Successfully updated file ${absolutePath}. ${replaceMsg} ${blocksFailed} block(s) failed (search criteria not found).`,
        updatedPath: absolutePath,
        blocksApplied,
        blocksFailed,
      };
    } else {
      // No replacements were made, even if blocks were provided
      logger.info(`updateFileLogic: No replacements made in file "${absolutePath}"`, { ...logicContext, requestedPath, blocksFailed });
      return {
        message: `No changes applied to file ${absolutePath}. ${blocksFailed} block(s) failed (search criteria not found).`,
        updatedPath: absolutePath,
        blocksApplied: 0, // No blocks resulted in a change
        blocksFailed,
      };
    }

  } catch (error: any) {
    logger.error(`updateFileLogic: Error updating file "${absolutePath}"`, { ...logicContext, requestedPath, error: error.message, code: error.code });
    if (error instanceof McpError) {
      throw error; // Re-throw known McpErrors
    }
    // Handle potential I/O errors during read or write
    throw new McpError(BaseErrorCode.INTERNAL_ERROR, `Failed to update file: ${error.message || 'Unknown I/O error'}`, { ...context, requestedPath, resolvedPath: absolutePath, originalError: error });
  }
};
