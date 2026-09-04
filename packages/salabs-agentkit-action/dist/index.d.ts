export interface MeshStats {
  vertex_count: number;
  face_count: number;
}

export interface GeneratedMeshResult {
  prompt: string;
  latency_ms: number;
  euler_characteristic: number;
  non_manifold_edges: number;
  assembly_components: string[];
  stats: MeshStats;
  vertices: number[][];
  faces: number[][];
  obj_format: string;
}

export class BishopFrameContinuumSolver {
  static computeBishopFrame(curve: number[][]): { tangents: number[][]; M1: number[][]; M2: number[][] };
}

export class SalabsArticulatedRoboticsGenerator {
  static generateMesh(prompt?: string, curveScale?: number): GeneratedMeshResult;
}

export class SalabsRegistryClient {
  static CONTRACT_ADDRESS: string;
  static MASTER_TREASURY: string;
  static BASE_RPC: string;
  static USDC_BASE: string;
  static queryToolInfo(slug?: string, rpcUrl?: string): Promise<string>;
}

export interface SalabsActionConfig {
  rpcUrl?: string;
  contractAddress?: string;
  treasuryAddress?: string;
  autoSettle?: boolean;
}

export interface ActionDefinition {
  name: string;
  description: string;
  schema: Record<string, any>;
  invoke: (args: any) => Promise<string>;
}

export class SalabsActionProvider {
  name: string;
  actionProviderName: string;
  config: SalabsActionConfig;
  constructor(config?: SalabsActionConfig);
  supportsNetwork(network: any): boolean;
  getActions(walletProvider?: any): ActionDefinition[];
}

export declare const salabsActionProvider: (config?: SalabsActionConfig) => SalabsActionProvider;
export default salabsActionProvider;
