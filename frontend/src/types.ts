export interface Run {
  id: string;
  idea: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_stage: string;
  product_name?: string;
  tagline?: string;
  preview_url?: string;
  deck_path?: string;
  narration_path?: string;
  started_at: string;
  finished_at?: string;
  metadata?: Record<string, any>;
}

export interface StageEvent {
  id: number;
  run_id: string;
  stage: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped';
  started_at?: string;
  finished_at?: string;
  input_json?: any;
  output_json?: any;
  error?: string;
  logs: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
}
