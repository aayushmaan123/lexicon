/**
 * Core AI Agent interface
 * 
 * All AI agents (DeepSeek, Google RAG, etc.) implement this interface
 * to ensure consistent behavior across the platform.
 */
export interface AIAgent {
  /**
   * Unique identifier for the agent type
   */
  readonly agentType: AgentType;

  /**
   * Initialize the agent with configuration
   * @param config Agent-specific configuration
   */
  initialize(config: AgentConfig): Promise<void>;

  /**
   * Execute a query using the agent
   * @param query User query or task
   * @returns Agent response
   */
  execute(query: AgentQuery): Promise<AgentResponse>;

  /**
   * Check if the agent is ready to process requests
   */
  isReady(): boolean;
}

/**
 * Types of AI agents supported by the platform
 */
export enum AgentType {
  DEEPSEEK = 'deepseek',
  GOOGLE_RAG = 'google_rag',
  ORCHESTRATOR = 'orchestrator',
}

/**
 * Base configuration for all agents
 */
export interface AgentConfig {
  apiKey?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  timeout?: number;
  [key: string]: unknown;
}

/**
 * Query structure for agent execution
 */
export interface AgentQuery {
  /**
   * The user's query or task
   */
  query: string;

  /**
   * Optional context for the query
   */
  context?: string[];

  /**
   * Additional metadata
   */
  metadata?: Record<string, unknown>;
}

/**
 * Response structure from agent execution
 */
export interface AgentResponse {
  /**
   * The agent's response content
   */
  content: string;

  /**
   * Confidence score (0-1)
   */
  confidence?: number;

  /**
   * Sources or citations used
   */
  sources?: Source[];

  /**
   * Additional metadata
   */
  metadata?: Record<string, unknown>;
}

/**
 * Source citation structure
 */
export interface Source {
  id: string;
  title: string;
  url?: string;
  snippet?: string;
  relevanceScore?: number;
}
