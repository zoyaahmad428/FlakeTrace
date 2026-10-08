export type Toolchain = {
  java: string;
  javac: string;
  mvn: string;
  evosuite_jar: string;
  can_run_tests: boolean;
  can_run_maven: boolean;
  can_run_evosuite: boolean;
  missing: string[];
};

export type Health = { status: string; git: boolean; toolchain: Toolchain; demo_project: boolean };

export type Source = {
  status: string;
  kind: string;
  path: string;
  name: string;
  is_git: boolean;
  module: string;
  java_files: number;
  test_files: number;
  note?: string;
  error?: string;
};

export type GitInfo = {
  status: string;
  sha: string;
  sha_full: string;
  branch: string;
  commits: [string, string, string][];
  error?: string;
};

export type Access = {
  test: string;
  method: string;
  file: string;
  line: number;
  code: string;
  attribution: "direct" | "indirect";
  how: string;
  restores?: boolean;
};

export type Resource = {
  owner: string;
  owner_fqcn: string;
  field: string;
  type: string;
  declared_at: string;
  id: string;
};

export type Finding = {
  resource: Resource;
  verdict: string;
  severity: "bad" | "warn" | "ok";
  summary: string;
  writers: Access[];
  readers: Access[];
  polluters: Access[];
  victims: Access[];
};

export type Suggested = {
  polluter: string;
  victim: string;
  resource: string;
  polluter_at: string;
  victim_at: string;
  order: string[];
};

export type Analysis = {
  status: string;
  counts: { production_classes: number; test_classes: number; test_methods: number; shared_statics: number };
  findings: Finding[];
  suggested: Suggested | null;
  test_classes: string[];
  test_methods: string[];
  error?: string;
};

export type RunResult = {
  status: string;
  exit_code?: number;
  passed?: boolean;
  output?: string;
  error?: string;
  command?: string;
  order?: string[];
};

export type PatchResult = {
  status: string;
  applied?: boolean;
  file?: string;
  resource?: string;
  polluter?: string;
  polluter_at?: string;
  victim?: string;
  diff?: string;
  added_lines?: number;
  strategy?: string;
  policy?: [string, boolean, string][];
  error?: string;
};

export type EvoParams = {
  targetClass: string;
  searchBudget: string;
  seed: string;
  criteria: string;
  assertionStrategy: string;
  deterministic: boolean;
};

export type EvoResult = {
  status: string;
  target_class?: string;
  suite_class?: string;
  command?: string;
  test_dir?: string;
  generated_files?: string[];
  error?: string;
  toolchain?: Toolchain;
};

export type Recorded = {
  health: Health;
  source: Source;
  git: GitInfo;
  analysis: Analysis;
  runs: Record<string, RunResult>;
  scan: { candidate: string; result: RunResult }[];
  patch: PatchResult;
  evosuite: EvoResult;
};
