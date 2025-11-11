/**
 * Display Rules Configuration
 *
 * This file defines how different types of results should be displayed.
 * Maps backend DisplayType and ResultFormat to frontend React components.
 */

import { DisplayType, OutputType, ResultFormat } from './nodeConfig';

/**
 * Display component type enum
 * Represents different ways to display node results
 */
export enum DisplayComponentType {
  TABLE = 'table',
  JSON_VIEWER = 'json_viewer',
  PLOTLY_CHART = 'plotly_chart',
  ECHARTS_CHART = 'echarts_chart',
  IMAGE_VIEWER = 'image_viewer',
  FUNCTION_INFO = 'function_info',
  EMPTY = 'empty'
}

/**
 * Configuration for how to display a result
 */
export interface DisplayRuleConfig {
  displayType: DisplayType;
  componentType: DisplayComponentType;
  props?: Record<string, any>;
  description: string;
}

/**
 * Display rules mapping backend DisplayType to frontend components
 */
export const DISPLAY_RULES: Record<DisplayType, DisplayRuleConfig> = {
  [DisplayType.TABLE]: {
    displayType: DisplayType.TABLE,
    componentType: DisplayComponentType.TABLE,
    props: {
      rowsPerPage: 10,
      sortable: true,
      filterable: true,
      exportable: true
    },
    description: 'Display as paginated HTML table'
  },
  [DisplayType.JSON_VIEWER]: {
    displayType: DisplayType.JSON_VIEWER,
    componentType: DisplayComponentType.JSON_VIEWER,
    props: {
      collapsed: false,
      highlightSyntax: true,
      copyable: true
    },
    description: 'Display as formatted JSON with syntax highlighting'
  },
  [DisplayType.PLOTLY_CHART]: {
    displayType: DisplayType.PLOTLY_CHART,
    componentType: DisplayComponentType.PLOTLY_CHART,
    props: {
      responsive: true,
      displayModeBar: true
    },
    description: 'Display as Plotly interactive chart'
  },
  [DisplayType.ECHARTS_CHART]: {
    displayType: DisplayType.ECHARTS_CHART,
    componentType: DisplayComponentType.ECHARTS_CHART,
    props: {
      responsive: true,
      showToolbox: true
    },
    description: 'Display as ECharts interactive visualization'
  },
  [DisplayType.IMAGE_VIEWER]: {
    displayType: DisplayType.IMAGE_VIEWER,
    componentType: DisplayComponentType.IMAGE_VIEWER,
    props: {
      maxWidth: '100%',
      fit: 'contain'
    },
    description: 'Display as image (PNG, JPG, GIF, etc.)'
  },
  [DisplayType.NONE]: {
    displayType: DisplayType.NONE,
    componentType: DisplayComponentType.EMPTY,
    props: {
      message: 'No result to display'
    },
    description: 'No display (function outputs, None values, etc.)'
  }
};

/**
 * Mapping from OutputType to appropriate DisplayType
 * This helps infer the best display method from the output type
 */
export const OUTPUT_TO_DISPLAY_TYPE: Record<OutputType, DisplayType> = {
  'dataframe': DisplayType.TABLE,
  'dict_list': DisplayType.JSON_VIEWER,
  'plotly': DisplayType.PLOTLY_CHART,
  'echarts': DisplayType.ECHARTS_CHART,
  'image': DisplayType.IMAGE_VIEWER,
  'function': DisplayType.NONE,
  'unknown': DisplayType.JSON_VIEWER
};

/**
 * Mapping from ResultFormat to expected file extensions and MIME types
 */
export interface ResultFormatInfo {
  format: ResultFormat;
  extensions: string[];
  mimeTypes: string[];
  binaryFormat: boolean;
}

export const RESULT_FORMAT_INFO: Record<ResultFormat, ResultFormatInfo> = {
  [ResultFormat.PARQUET]: {
    format: ResultFormat.PARQUET,
    extensions: ['.parquet'],
    mimeTypes: ['application/octet-stream'],
    binaryFormat: true
  },
  [ResultFormat.JSON]: {
    format: ResultFormat.JSON,
    extensions: ['.json'],
    mimeTypes: ['application/json'],
    binaryFormat: false
  },
  [ResultFormat.IMAGE]: {
    format: ResultFormat.IMAGE,
    extensions: ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'],
    mimeTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/svg+xml', 'image/webp'],
    binaryFormat: true
  },
  [ResultFormat.NONE]: {
    format: ResultFormat.NONE,
    extensions: [],
    mimeTypes: [],
    binaryFormat: false
  }
};

/**
 * Get display rule for a given DisplayType
 */
export function getDisplayRule(displayType: DisplayType): DisplayRuleConfig {
  return DISPLAY_RULES[displayType] || DISPLAY_RULES[DisplayType.NONE];
}

/**
 * Get display component type for a given DisplayType
 */
export function getDisplayComponentType(displayType: DisplayType): DisplayComponentType {
  return getDisplayRule(displayType).componentType;
}

/**
 * Infer DisplayType from OutputType
 * Helps when backend doesn't explicitly provide DisplayType
 */
export function inferDisplayType(outputType: OutputType): DisplayType {
  return OUTPUT_TO_DISPLAY_TYPE[outputType] || DisplayType.NONE;
}

/**
 * Get display rule from OutputType (convenience function)
 */
export function getDisplayRuleFromOutputType(outputType: OutputType): DisplayRuleConfig {
  const displayType = inferDisplayType(outputType);
  return getDisplayRule(displayType);
}

/**
 * Check if a result format is binary (requires special handling)
 */
export function isBinaryFormat(format: ResultFormat): boolean {
  return RESULT_FORMAT_INFO[format]?.binaryFormat || false;
}

/**
 * Get expected MIME type for a result format
 */
export function getMimeTypeForFormat(format: ResultFormat): string {
  const info = RESULT_FORMAT_INFO[format];
  return info?.mimeTypes[0] || 'application/octet-stream';
}

/**
 * Preset display configurations
 * These can be used as templates for common display scenarios
 */
export const DISPLAY_PRESETS = {
  /**
   * Default table display with standard settings
   */
  defaultTable: {
    displayType: DisplayType.TABLE,
    props: {
      rowsPerPage: 10,
      sortable: true,
      filterable: true,
      exportable: true
    }
  },

  /**
   * Compact table display for smaller screens
   */
  compactTable: {
    displayType: DisplayType.TABLE,
    props: {
      rowsPerPage: 5,
      sortable: true,
      filterable: false,
      exportable: false
    }
  },

  /**
   * Large table display for data exploration
   */
  largeTable: {
    displayType: DisplayType.TABLE,
    props: {
      rowsPerPage: 50,
      sortable: true,
      filterable: true,
      exportable: true,
      columnResizable: true
    }
  },

  /**
   * Interactive Plotly chart
   */
  plotlyChart: {
    displayType: DisplayType.PLOTLY_CHART,
    props: {
      responsive: true,
      displayModeBar: true,
      displaylogo: false
    }
  },

  /**
   * ECharts visualization with toolbar
   */
  echartsChart: {
    displayType: DisplayType.ECHARTS_CHART,
    props: {
      responsive: true,
      showToolbox: true,
      showLegend: true
    }
  },

  /**
   * Full-screen image display
   */
  fullscreenImage: {
    displayType: DisplayType.IMAGE_VIEWER,
    props: {
      maxWidth: '100%',
      fit: 'contain',
      fullscreen: true
    }
  },

  /**
   * Thumbnail image display
   */
  thumbnailImage: {
    displayType: DisplayType.IMAGE_VIEWER,
    props: {
      maxWidth: '300px',
      fit: 'cover'
    }
  }
};
