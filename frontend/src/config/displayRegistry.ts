/**
 * Display Registry Configuration
 *
 * This file maps result formats to their corresponding React display components.
 * Each format knows:
 * - Which component to use for rendering
 * - How to load the data from the API
 * - What MIME types it handles
 *
 * When adding a new result format:
 * 1. Create a new Display component in src/components/displays/
 * 2. Add an entry to RESULT_FORMAT_DISPLAY_MAP
 * 3. Register the loader in RESULT_FORMAT_LOADERS
 */

import { ResultFormat } from './nodeConfig';

/**
 * Configuration for displaying a specific result format
 */
export interface DisplayFormatConfig {
  format: ResultFormat;
  componentName: string;      // Name of the component (e.g., 'TableDisplay', 'ImageDisplay')
  loaderName: string;         // Name of the loader function
  mimeTypes: string[];        // MIME types this format handles
  binaryFormat: boolean;      // Whether this is a binary format (requires special handling)
  showCodePanel?: boolean;    // Whether to show code/result toggle panel (default: true)
  defaultPanel?: 'code' | 'result';  // Default panel to show when node is selected (default: 'result')
  loadResultData?: boolean;   // Whether to call getNodeData to load result (default: true)
}

/**
 * Registry mapping result formats to display configurations
 *
 * Each entry defines:
 * - Which React component renders this format
 * - How to load the data
 * - What file types it handles
 */
export const RESULT_FORMAT_DISPLAY_MAP: Record<ResultFormat, DisplayFormatConfig> = {
  [ResultFormat.PARQUET]: {
    format: ResultFormat.PARQUET,
    componentName: 'TableDisplay',
    loaderName: 'loadParquetData',
    mimeTypes: ['application/octet-stream'],
    binaryFormat: true,
  },

  [ResultFormat.JSON]: {
    format: ResultFormat.JSON,
    componentName: 'JsonDisplay',
    loaderName: 'loadJsonData',
    mimeTypes: ['application/json'],
    binaryFormat: false,
  },

  [ResultFormat.IMAGE]: {
    format: ResultFormat.IMAGE,
    componentName: 'ImageDisplay',
    loaderName: 'loadImageData',
    mimeTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml'],
    binaryFormat: true,
  },

  [ResultFormat.PKL]: {
    format: ResultFormat.PKL,
    componentName: 'FunctionInfoDisplay',
    loaderName: 'loadPklData',
    mimeTypes: ['application/octet-stream'],
    binaryFormat: true,
    showCodePanel: false,      // Don't show code/result toggle button for tool nodes
    defaultPanel: 'code',      // Default to showing code
    loadResultData: false,     // Don't attempt to load result data via API
  },

  [ResultFormat.NONE]: {
    format: ResultFormat.NONE,
    componentName: 'EmptyDisplay',
    loaderName: 'loadNoneData',
    mimeTypes: [],
    binaryFormat: false,
  },
};

/**
 * Get display configuration for a result format
 */
export function getDisplayFormatConfig(format: ResultFormat | string): DisplayFormatConfig | null {
  return RESULT_FORMAT_DISPLAY_MAP[format as ResultFormat] || null;
}

/**
 * Get the component name for a result format
 */
export function getComponentNameForFormat(format: ResultFormat | string): string | null {
  const config = getDisplayFormatConfig(format);
  return config?.componentName || null;
}

/**
 * Get the loader name for a result format
 */
export function getLoaderNameForFormat(format: ResultFormat | string): string | null {
  const config = getDisplayFormatConfig(format);
  return config?.loaderName || null;
}

/**
 * Check if a format is binary (requires special handling)
 */
export function isBinaryResultFormat(format: ResultFormat | string): boolean {
  const config = getDisplayFormatConfig(format);
  return config?.binaryFormat || false;
}

/**
 * List all registered result formats
 */
export function getRegisteredFormats(): ResultFormat[] {
  return Object.keys(RESULT_FORMAT_DISPLAY_MAP) as ResultFormat[];
}

/**
 * Check if a format should show the code/result toggle panel
 */
export function shouldShowCodePanel(format: ResultFormat | string): boolean {
  const config = getDisplayFormatConfig(format);
  return config?.showCodePanel !== false;  // Default to true if not specified
}

/**
 * Get the default panel to show for a format
 */
export function getDefaultPanel(format: ResultFormat | string): 'code' | 'result' {
  const config = getDisplayFormatConfig(format);
  return config?.defaultPanel || 'result';  // Default to result if not specified
}

/**
 * Check if a format requires loading result data via API
 */
export function shouldLoadResultData(format: ResultFormat | string): boolean {
  const config = getDisplayFormatConfig(format);
  return config?.loadResultData !== false;  // Default to true if not specified
}
