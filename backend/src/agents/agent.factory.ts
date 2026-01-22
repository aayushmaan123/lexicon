import { AIAgent, AgentType } from '@lexicon/shared';
import { DeepSeekAgent } from './deepseek.agent';
import { GoogleRAGAgent } from './google-rag.agent';

/**
 * Agent Factory
 * 
 * Creates and manages AI agent instances
 */
export class AgentFactory {
  private static agents: Map<AgentType, AIAgent> = new Map();

  /**
   * Get or create an agent instance
   */
  public static getAgent(type: AgentType): AIAgent {
    if (!this.agents.has(type)) {
      const agent = this.createAgent(type);
      this.agents.set(type, agent);
    }

    return this.agents.get(type)!;
  }

  /**
   * Create a new agent instance
   */
  private static createAgent(type: AgentType): AIAgent {
    switch (type) {
      case AgentType.DEEPSEEK:
        return new DeepSeekAgent();
      case AgentType.GOOGLE_RAG:
        return new GoogleRAGAgent();
      default:
        throw new Error(`Unknown agent type: ${type}`);
    }
  }

  /**
   * Clear all agent instances (useful for testing)
   */
  public static clearAgents(): void {
    this.agents.clear();
  }
}
