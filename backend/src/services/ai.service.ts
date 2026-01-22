import { AgentQuery, AgentResponse, AgentType } from '@lexicon/shared';
import { AgentFactory } from '../agents/agent.factory';

/**
 * AI Service
 * 
 * Orchestrates AI agents and handles query routing
 * 
 * TODO Phase 2: Implement advanced orchestration
 * - Add query routing logic
 * - Implement multi-agent coordination
 * - Add response synthesis from multiple agents
 * - Implement caching
 * - Add rate limiting
 */
export class AIService {
  /**
   * Execute a query using the specified agent
   */
  public async executeQuery(agentType: AgentType, query: AgentQuery): Promise<AgentResponse> {
    const agent = AgentFactory.getAgent(agentType);

    if (!agent.isReady()) {
      // TODO Phase 2: Get API keys from secure config/secrets manager
      await agent.initialize({});
    }

    return await agent.execute(query);
  }

  /**
   * Execute a query using DeepSeek
   */
  public async queryDeepSeek(query: AgentQuery): Promise<AgentResponse> {
    return this.executeQuery(AgentType.DEEPSEEK, query);
  }

  /**
   * Execute a query using Google RAG
   */
  public async queryGoogleRAG(query: AgentQuery): Promise<AgentResponse> {
    return this.executeQuery(AgentType.GOOGLE_RAG, query);
  }

  /**
   * Execute a hybrid query (both DeepSeek and RAG)
   * 
   * TODO Phase 2: Implement actual hybrid query logic
   * - Combine results from multiple agents
   * - Implement result synthesis
   * - Add confidence scoring
   */
  public async hybridQuery(_query: AgentQuery): Promise<AgentResponse> {
    // TODO Phase 2: Implement hybrid query
    throw new Error('Hybrid query not implemented - Phase 2');
  }
}

export const aiService = new AIService();
