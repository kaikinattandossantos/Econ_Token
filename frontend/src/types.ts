export interface TokenBreakdownItem {
  label: string;
  tokens: number;
  input_tokens?: number;
  output_tokens?: number;
  percentage: number;
  credits: number;
  credit_percentage: number;
}

export interface UsageData {
  route: string;
  tokens: {
    local_input: number;
    local_output: number;
    local_total: number;
    remote_input: number;
    remote_output: number;
    remote_total: number;
    total: number;
  };
  credits: {
    total_spent: number;
    remote_only: number;
    saved_vs_always_remote: number;
    breakdown: TokenBreakdownItem[];
  };
  local_calls: number;
}

export interface ChatResponse {
  answer: string;
  route: string;
  difficulty_score: number;
  local_confidence: number;
  local_model: string;
  remote_model: string;
  usage: UsageData;
}

export interface SessionStats {
  total_tokens: number;
  total_credits: number;
  local_tokens: number;
  remote_tokens: number;
  messages: number;
  token_breakdown: TokenBreakdownItem[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  usage?: UsageData;
  route?: string;
  isLoading?: boolean;
}