import { z } from 'zod';
import { McpError } from '../../../types-global/errors.js';
import { RequestContext } from '../../../utils/internal/requestContext.js';
import { serverState } from '../../state.js'; // Import the server state

// Define the input schema using Zod for validation
export const SetFilesystemDefaultInputSchema = z.object({
  path: z.string().min(1, 'Path cannot be empty')
    .describe('The absolute path to set as the default for resolving relative paths during this session.'),
});

// Define the TypeScript type for the input
export type SetFilesystemDefaultInput = z.infer<typeof SetFilesystemDefaultInputSchema>;

// Define the TypeScript type for the output (simple success message)
export interface SetFilesystemDefaultOutput {
  message: string;
  currentDefaultPath: string | null;
}

/**
 * Sets the default filesystem path for the current session.
 *
 * @param {SetFilesystemDefaultInput} input - The input object containing the absolute path.
 * @param {RequestContext} context - The request context for logging and error handling.
 * @returns {Promise<SetFilesystemDefaultOutput>} A promise that resolves with a success message and the new default path.
 * @throws {McpError} Throws McpError if the path is invalid or not absolute.
 */
export const setFilesystemDefaultLogic = async (input: SetFilesystemDefaultInput, context: RequestContext): Promise<SetFilesystemDefaultOutput> => {
  const { path: newPath } = input;

  // The validation (absolute check, sanitization) happens within serverState.setDefaultFilesystemPath
  serverState.setDefaultFilesystemPath(newPath, context);

  const currentPath = serverState.getDefaultFilesystemPath();
  return {
    message: `Default filesystem path successfully set to: ${currentPath}`,
    currentDefaultPath: currentPath,
  };
};
