/**
 * K-12 CS Framework — Canonical Concept & Task Catalog
 *
 * Single source of truth for:
 *  - K-12 CS concept definitions (id, grade_band, concept_area, difficulty)
 *  - Prerequisite DAG (mirrors concept_dependencies table in Postgres)
 *  - Task bank: real MCQ questions per concept (frontend demo / offline mode)
 *  - Learning path helpers
 *
 * Standards alignment:
 *  - CSTA 2017 (K-12 CS Framework)
 *  - ISTE Student Standards 2016
 *  - Indonesian Informatika — Kurikulum Merdeka (2022)
 *    Areas: BK (Berpikir Komputasional), AP (Algoritma & Pemrograman),
 *           SK (Sistem Komputer), JKI (Jaringan & Internet),
 *           AD (Analisis Data), DSI (Dampak Sosial Informatika)
 *
 * Concept ID convention:
 *   {grade_band}_{concept_area}
 *   grade_bands: k2 | k5 | k8 | k12
 *   (matches exact IDs seeded in concept_dependencies / k12_concepts tables)
 */

// ─── Type definitions ─────────────────────────────────────────────────────────

export type GradeBand = 'K-2' | 'K-5' | 'K-8' | 'K-12'

export type ConceptArea =
  | 'Algorithms'
  | 'Control Structures'
  | 'Variables'
  | 'Modularity'
  | 'Program Development'
  | 'Computing Systems'
  | 'Networks'
  | 'Data Analysis'
  | 'Social Impacts'

export interface K12Concept {
  id: string
  gradeBand: GradeBand
  conceptArea: ConceptArea
  cognitiveLevel: 1 | 2 | 3 | 4     // Bloom's: 1=Remember, 2=Understand, 3=Apply/Analyze, 4=Evaluate/Create
  difficulty: number                  // 0–1
  label: string                       // Short display name
  description: string                 // One-line learning goal
  cstaStandard: string                // e.g. "CSTA 1A-AP-08"
  indonesianStandard: string          // e.g. "AP-K2-1" (AP = Algoritma & Pemrograman)
  prerequisites: string[]             // Other concept IDs
}

export interface ConceptEdge {
  source: string
  target: string
  transferWeight: number              // 0–1, mirrors transfer_weight in concept_dependencies
  dependencyType: 'prerequisite' | 'related' | 'advanced'
}

export interface K12Task {
  id: string
  conceptId: string
  taskType: 'mpq' | 'text' | 'code'
  title: string
  questionText: string
  choices: string[]                   // 4 options for MPQ
  correctAnswer: string               // Must match one of choices exactly
  explanation: string
  difficulty: number
  cognitiveLevel: 1 | 2 | 3 | 4
}

// ─── Concept Catalog ──────────────────────────────────────────────────────────
// 36 canonical concepts across 9 areas × 4 grade bands (K-12 band partial)

export const K12_CONCEPTS: K12Concept[] = [

  // ── Algorithms ────────────────────────────────────────────────────────────
  {
    id: 'k2_algorithms',
    gradeBand: 'K-2', conceptArea: 'Algorithms',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Algorithms (K-2)',
    description: 'Understand and follow step-by-step instructions to solve simple problems',
    cstaStandard: 'CSTA 1A-AP-08',
    indonesianStandard: 'BK-K2-1',
    prerequisites: [],
  },
  {
    id: 'k5_algorithms',
    gradeBand: 'K-5', conceptArea: 'Algorithms',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Algorithms (K-5)',
    description: 'Design and trace simple algorithms; recognize loops and sequences',
    cstaStandard: 'CSTA 1B-AP-08',
    indonesianStandard: 'AP-K5-1',
    prerequisites: ['k2_algorithms'],
  },
  {
    id: 'k8_algorithms',
    gradeBand: 'K-8', conceptArea: 'Algorithms',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Algorithms (K-8)',
    description: 'Analyze and compare algorithm efficiency; understand time/space trade-offs',
    cstaStandard: 'CSTA 2-AP-10',
    indonesianStandard: 'AP-K8-2',
    prerequisites: ['k5_algorithms'],
  },
  {
    id: 'k12_algorithms',
    gradeBand: 'K-12', conceptArea: 'Algorithms',
    cognitiveLevel: 4, difficulty: 0.80,
    label: 'Algorithms (K-12)',
    description: 'Design advanced algorithms; reason about worst-case complexity and optimization',
    cstaStandard: 'CSTA 3A-AP-10',
    indonesianStandard: 'AP-K12-3',
    prerequisites: ['k8_algorithms'],
  },

  // ── Control Structures ────────────────────────────────────────────────────
  {
    id: 'k2_control',
    gradeBand: 'K-2', conceptArea: 'Control Structures',
    cognitiveLevel: 1, difficulty: 0.25,
    label: 'Control Structures (K-2)',
    description: 'Recognize and use repetition and simple conditionals in everyday tasks',
    cstaStandard: 'CSTA 1A-AP-10',
    indonesianStandard: 'BK-K2-2',
    prerequisites: ['k2_algorithms'],
  },
  {
    id: 'k5_control',
    gradeBand: 'K-5', conceptArea: 'Control Structures',
    cognitiveLevel: 2, difficulty: 0.45,
    label: 'Control Structures (K-5)',
    description: 'Create programs with loops and conditionals; trace control flow',
    cstaStandard: 'CSTA 1B-AP-10',
    indonesianStandard: 'AP-K5-2',
    prerequisites: ['k2_control', 'k5_algorithms'],
  },
  {
    id: 'k8_control',
    gradeBand: 'K-8', conceptArea: 'Control Structures',
    cognitiveLevel: 3, difficulty: 0.65,
    label: 'Control Structures (K-8)',
    description: 'Use nested loops, boolean logic, and event-driven control flow',
    cstaStandard: 'CSTA 2-AP-11',
    indonesianStandard: 'AP-K8-3',
    prerequisites: ['k5_control', 'k8_algorithms'],
  },
  {
    id: 'k12_control',
    gradeBand: 'K-12', conceptArea: 'Control Structures',
    cognitiveLevel: 4, difficulty: 0.80,
    label: 'Control Structures (K-12)',
    description: 'Analyze nested control flow; reason about complexity from loop structures',
    cstaStandard: 'CSTA 3A-AP-11',
    indonesianStandard: 'AP-K12-4',
    prerequisites: ['k8_control'],
  },

  // ── Variables ─────────────────────────────────────────────────────────────
  {
    id: 'k2_variables',
    gradeBand: 'K-2', conceptArea: 'Variables',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Variables (K-2)',
    description: 'Understand that variables store values that can change in programs',
    cstaStandard: 'CSTA 1A-AP-09',
    indonesianStandard: 'AP-K2-2',
    prerequisites: [],
  },
  {
    id: 'k5_variables',
    gradeBand: 'K-5', conceptArea: 'Variables',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Variables (K-5)',
    description: 'Use variables of different types; understand assignment and scope',
    cstaStandard: 'CSTA 1B-AP-09',
    indonesianStandard: 'AP-K5-3',
    prerequisites: ['k2_variables'],
  },
  {
    id: 'k8_variables',
    gradeBand: 'K-8', conceptArea: 'Variables',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Variables (K-8)',
    description: 'Manage complex data types, lists, and scope in multi-function programs',
    cstaStandard: 'CSTA 2-AP-09',
    indonesianStandard: 'AP-K8-4',
    prerequisites: ['k5_variables'],
  },

  // ── Modularity ────────────────────────────────────────────────────────────
  {
    id: 'k2_modularity',
    gradeBand: 'K-2', conceptArea: 'Modularity',
    cognitiveLevel: 1, difficulty: 0.25,
    label: 'Modularity (K-2)',
    description: 'Decompose large problems into smaller, manageable parts',
    cstaStandard: 'CSTA 1A-AP-14',
    indonesianStandard: 'BK-K2-3',
    prerequisites: ['k2_algorithms'],
  },
  {
    id: 'k5_modularity',
    gradeBand: 'K-5', conceptArea: 'Modularity',
    cognitiveLevel: 2, difficulty: 0.45,
    label: 'Modularity (K-5)',
    description: 'Create reusable procedures; understand parameters and return values',
    cstaStandard: 'CSTA 1B-AP-14',
    indonesianStandard: 'AP-K5-4',
    prerequisites: ['k2_modularity', 'k5_algorithms'],
  },
  {
    id: 'k8_modularity',
    gradeBand: 'K-8', conceptArea: 'Modularity',
    cognitiveLevel: 3, difficulty: 0.65,
    label: 'Modularity (K-8)',
    description: 'Design modular programs with abstraction layers; debug across modules',
    cstaStandard: 'CSTA 2-AP-14',
    indonesianStandard: 'AP-K8-5',
    prerequisites: ['k5_modularity', 'k8_algorithms'],
  },

  // ── Program Development ───────────────────────────────────────────────────
  {
    id: 'k2_program_development',
    gradeBand: 'K-2', conceptArea: 'Program Development',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Program Development (K-2)',
    description: 'Use and modify simple programs; understand testing and debugging basics',
    cstaStandard: 'CSTA 1A-AP-15',
    indonesianStandard: 'AP-K2-3',
    prerequisites: ['k2_algorithms'],
  },
  {
    id: 'k5_program_development',
    gradeBand: 'K-5', conceptArea: 'Program Development',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Program Development (K-5)',
    description: 'Plan, write, test, and debug programs systematically',
    cstaStandard: 'CSTA 1B-AP-15',
    indonesianStandard: 'AP-K5-5',
    prerequisites: ['k2_program_development', 'k5_algorithms'],
  },
  {
    id: 'k8_program_development',
    gradeBand: 'K-8', conceptArea: 'Program Development',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Program Development (K-8)',
    description: 'Apply iterative design; use version control and collaborative development',
    cstaStandard: 'CSTA 2-AP-15',
    indonesianStandard: 'AP-K8-6',
    prerequisites: ['k5_program_development', 'k8_modularity'],
  },

  // ── Computing Systems ─────────────────────────────────────────────────────
  {
    id: 'k2_computing_systems_devices',
    gradeBand: 'K-2', conceptArea: 'Computing Systems',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Computing Systems (K-2)',
    description: 'Identify computing devices and distinguish hardware from software',
    cstaStandard: 'CSTA 1A-CS-01',
    indonesianStandard: 'SK-K2-1',
    prerequisites: [],
  },
  {
    id: 'k5_computing_systems_devices',
    gradeBand: 'K-5', conceptArea: 'Computing Systems',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Computing Systems (K-5)',
    description: 'Explain how hardware components interact with software to run programs',
    cstaStandard: 'CSTA 1B-CS-01',
    indonesianStandard: 'SK-K5-1',
    prerequisites: ['k2_computing_systems_devices'],
  },
  {
    id: 'k8_computing_systems_devices',
    gradeBand: 'K-8', conceptArea: 'Computing Systems',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Computing Systems (K-8)',
    description: 'Analyze system architectures; understand CPU, memory, and I/O interactions',
    cstaStandard: 'CSTA 2-CS-01',
    indonesianStandard: 'SK-K8-2',
    prerequisites: ['k5_computing_systems_devices'],
  },

  // ── Networks ──────────────────────────────────────────────────────────────
  {
    id: 'k2_networks_communication',
    gradeBand: 'K-2', conceptArea: 'Networks',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Networks (K-2)',
    description: 'Identify basic network types and understand how devices communicate',
    cstaStandard: 'CSTA 1A-NI-04',
    indonesianStandard: 'JKI-K2-1',
    prerequisites: ['k2_computing_systems_devices'],
  },
  {
    id: 'k5_networks_communication',
    gradeBand: 'K-5', conceptArea: 'Networks',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Networks (K-5)',
    description: 'Explain how data travels across networks using protocols and packets',
    cstaStandard: 'CSTA 1B-NI-04',
    indonesianStandard: 'JKI-K5-1',
    prerequisites: ['k2_networks_communication', 'k5_computing_systems_devices'],
  },
  {
    id: 'k8_networks_communication',
    gradeBand: 'K-8', conceptArea: 'Networks',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Networks (K-8)',
    description: 'Model network protocols, IP addressing, and basic cybersecurity concepts',
    cstaStandard: 'CSTA 2-NI-04',
    indonesianStandard: 'JKI-K8-2',
    prerequisites: ['k5_networks_communication'],
  },

  // ── Data Analysis ─────────────────────────────────────────────────────────
  {
    id: 'k2_data_collection',
    gradeBand: 'K-2', conceptArea: 'Data Analysis',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Data Analysis (K-2)',
    description: 'Collect and represent simple data using charts and tables',
    cstaStandard: 'CSTA 1A-DA-06',
    indonesianStandard: 'AD-K2-1',
    prerequisites: [],
  },
  {
    id: 'k5_data_collection',
    gradeBand: 'K-5', conceptArea: 'Data Analysis',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Data Analysis (K-5)',
    description: 'Collect, organize, and analyze data to answer questions; identify patterns',
    cstaStandard: 'CSTA 1B-DA-06',
    indonesianStandard: 'AD-K5-1',
    prerequisites: ['k2_data_collection'],
  },
  {
    id: 'k8_data_collection',
    gradeBand: 'K-8', conceptArea: 'Data Analysis',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Data Analysis (K-8)',
    description: 'Apply statistical analysis; clean and transform data for visualization',
    cstaStandard: 'CSTA 2-DA-08',
    indonesianStandard: 'AD-K8-2',
    prerequisites: ['k5_data_collection'],
  },
  {
    id: 'k12_data_collection',
    gradeBand: 'K-12', conceptArea: 'Data Analysis',
    cognitiveLevel: 4, difficulty: 0.80,
    label: 'Data Analysis (K-12)',
    description: 'Design data pipelines; understand machine learning concepts and bias',
    cstaStandard: 'CSTA 3A-DA-10',
    indonesianStandard: 'AD-K12-3',
    prerequisites: ['k8_data_collection'],
  },

  // ── Social Impacts ────────────────────────────────────────────────────────
  {
    id: 'k2_culture',
    gradeBand: 'K-2', conceptArea: 'Social Impacts',
    cognitiveLevel: 1, difficulty: 0.20,
    label: 'Social Impacts (K-2)',
    description: 'Identify positive and negative effects of technology in daily life',
    cstaStandard: 'CSTA 1A-IC-16',
    indonesianStandard: 'DSI-K2-1',
    prerequisites: [],
  },
  {
    id: 'k5_culture',
    gradeBand: 'K-5', conceptArea: 'Social Impacts',
    cognitiveLevel: 2, difficulty: 0.40,
    label: 'Social Impacts (K-5)',
    description: 'Analyze how computing affects society, culture, and the economy',
    cstaStandard: 'CSTA 1B-IC-18',
    indonesianStandard: 'DSI-K5-1',
    prerequisites: ['k2_culture'],
  },
  {
    id: 'k8_culture',
    gradeBand: 'K-8', conceptArea: 'Social Impacts',
    cognitiveLevel: 3, difficulty: 0.60,
    label: 'Social Impacts (K-8)',
    description: 'Evaluate privacy, security, and ethical implications of computing',
    cstaStandard: 'CSTA 2-IC-21',
    indonesianStandard: 'DSI-K8-2',
    prerequisites: ['k5_culture'],
  },
]

// ─── DAG Edges ────────────────────────────────────────────────────────────────
// Mirrors concept_dependencies table. transfer_weight = expected mastery transfer.

export const K12_EDGES: ConceptEdge[] = [
  // Algorithms progression
  { source: 'k2_algorithms',  target: 'k5_algorithms',  transferWeight: 0.85, dependencyType: 'prerequisite' },
  { source: 'k5_algorithms',  target: 'k8_algorithms',  transferWeight: 0.80, dependencyType: 'prerequisite' },
  { source: 'k8_algorithms',  target: 'k12_algorithms', transferWeight: 0.75, dependencyType: 'prerequisite' },
  { source: 'k2_algorithms',  target: 'k8_algorithms',  transferWeight: 0.65, dependencyType: 'advanced' },

  // Control structures progression
  { source: 'k2_control',     target: 'k5_control',     transferWeight: 0.80, dependencyType: 'prerequisite' },
  { source: 'k5_control',     target: 'k8_control',     transferWeight: 0.78, dependencyType: 'prerequisite' },
  { source: 'k8_control',     target: 'k12_control',    transferWeight: 0.72, dependencyType: 'prerequisite' },

  // Cross-strand: algorithms → control
  { source: 'k2_algorithms',  target: 'k2_control',     transferWeight: 0.55, dependencyType: 'related' },
  { source: 'k5_algorithms',  target: 'k5_control',     transferWeight: 0.50, dependencyType: 'related' },
  { source: 'k8_algorithms',  target: 'k8_control',     transferWeight: 0.45, dependencyType: 'related' },

  // Variables progression
  { source: 'k2_variables',   target: 'k5_variables',   transferWeight: 0.80, dependencyType: 'prerequisite' },
  { source: 'k5_variables',   target: 'k8_variables',   transferWeight: 0.75, dependencyType: 'prerequisite' },
  { source: 'k5_variables',   target: 'k5_control',     transferWeight: 0.45, dependencyType: 'related' },

  // Modularity progression
  { source: 'k2_modularity',  target: 'k5_modularity',  transferWeight: 0.70, dependencyType: 'prerequisite' },
  { source: 'k5_modularity',  target: 'k8_modularity',  transferWeight: 0.68, dependencyType: 'prerequisite' },
  { source: 'k5_algorithms',  target: 'k5_modularity',  transferWeight: 0.40, dependencyType: 'related' },
  { source: 'k8_modularity',  target: 'k8_program_development', transferWeight: 0.50, dependencyType: 'related' },

  // Program development
  { source: 'k2_program_development', target: 'k5_program_development', transferWeight: 0.75, dependencyType: 'prerequisite' },
  { source: 'k5_program_development', target: 'k8_program_development', transferWeight: 0.70, dependencyType: 'prerequisite' },
  { source: 'k5_control',     target: 'k5_program_development', transferWeight: 0.42, dependencyType: 'related' },

  // Computing systems
  { source: 'k2_computing_systems_devices', target: 'k5_computing_systems_devices', transferWeight: 0.88, dependencyType: 'prerequisite' },
  { source: 'k5_computing_systems_devices', target: 'k8_computing_systems_devices', transferWeight: 0.80, dependencyType: 'prerequisite' },

  // Networks
  { source: 'k2_networks_communication', target: 'k5_networks_communication', transferWeight: 0.82, dependencyType: 'prerequisite' },
  { source: 'k5_networks_communication', target: 'k8_networks_communication', transferWeight: 0.78, dependencyType: 'prerequisite' },
  { source: 'k5_computing_systems_devices', target: 'k5_networks_communication', transferWeight: 0.40, dependencyType: 'related' },

  // Data analysis
  { source: 'k2_data_collection', target: 'k5_data_collection', transferWeight: 0.85, dependencyType: 'prerequisite' },
  { source: 'k5_data_collection', target: 'k8_data_collection', transferWeight: 0.78, dependencyType: 'prerequisite' },
  { source: 'k8_data_collection', target: 'k12_data_collection', transferWeight: 0.72, dependencyType: 'prerequisite' },
  { source: 'k8_algorithms',  target: 'k8_data_collection',   transferWeight: 0.38, dependencyType: 'related' },

  // Social impacts
  { source: 'k2_culture',     target: 'k5_culture',     transferWeight: 0.75, dependencyType: 'prerequisite' },
  { source: 'k5_culture',     target: 'k8_culture',     transferWeight: 0.68, dependencyType: 'prerequisite' },
]

// ─── Task Bank ────────────────────────────────────────────────────────────────
// Real MPQ questions per concept — used as frontend demo/offline tasks.
// content JSONB format matches what the ITS runtime service expects:
//   { question, choices, correct_answer, explanation }

export const K12_TASKS: K12Task[] = [

  // ── k2_algorithms ────────────────────────────────────────────────────────
  {
    id: 'k2_algo_q1', conceptId: 'k2_algorithms', taskType: 'mpq',
    title: 'What is an Algorithm?',
    questionText: 'Rina wants to make a cup of instant noodles. She needs to do these steps in order: boil water, open the packet, pour noodles, add seasoning, wait 3 minutes. What does this ordered set of steps represent?',
    choices: ['A recipe that can change any time', 'An algorithm — a clear step-by-step plan', 'A random list of ideas', 'A picture of noodles'],
    correctAnswer: 'An algorithm — a clear step-by-step plan',
    explanation: 'An algorithm is a precise sequence of steps to solve a problem. Ordered cooking instructions are a classic example.',
    difficulty: 0.20, cognitiveLevel: 1,
  },
  {
    id: 'k2_algo_q2', conceptId: 'k2_algorithms', taskType: 'mpq',
    title: 'Order Matters',
    questionText: 'A program should: (1) print "Hello", (2) print "World". If the steps run in reverse order, what happens?',
    choices: ['Nothing changes', '"World" prints before "Hello"', 'The program crashes', '"Hello World" prints on one line'],
    correctAnswer: '"World" prints before "Hello"',
    explanation: 'In an algorithm, order matters. Reversing the steps produces reversed output.',
    difficulty: 0.25, cognitiveLevel: 1,
  },
  {
    id: 'k2_algo_q3', conceptId: 'k2_algorithms', taskType: 'mpq',
    title: 'Algorithm vs. Story',
    questionText: 'Which of the following is the best example of an algorithm?',
    choices: [
      'Once upon a time there was a robot named Budi.',
      'Step 1: Pick up the ball. Step 2: Walk to the basket. Step 3: Drop the ball.',
      'A colorful picture of a playground.',
      'A list of all the children in the class.',
    ],
    correctAnswer: 'Step 1: Pick up the ball. Step 2: Walk to the basket. Step 3: Drop the ball.',
    explanation: 'An algorithm has clear, ordered steps with a goal. Options with narrative or images are not algorithms.',
    difficulty: 0.22, cognitiveLevel: 1,
  },

  // ── k5_algorithms ────────────────────────────────────────────────────────
  {
    id: 'k5_algo_q1', conceptId: 'k5_algorithms', taskType: 'mpq',
    title: 'Tracing a Loop',
    questionText: 'A loop runs the instruction "add 2 to total" exactly 5 times, starting with total = 0. What is the final value of total?',
    choices: ['5', '7', '10', '2'],
    correctAnswer: '10',
    explanation: 'Each iteration adds 2: 0→2→4→6→8→10. After 5 iterations the total is 10.',
    difficulty: 0.38, cognitiveLevel: 2,
  },
  {
    id: 'k5_algo_q2', conceptId: 'k5_algorithms', taskType: 'mpq',
    title: 'Choosing the Efficient Algorithm',
    questionText: 'Budi has a sorted list of 100 names. He wants to find "Zainul". Which approach is faster?',
    choices: [
      'Check every name from the beginning (linear search)',
      'Open the list at the middle, then narrow down (binary search)',
      'Shuffle the list first, then search',
      'Ask a friend to look instead',
    ],
    correctAnswer: 'Open the list at the middle, then narrow down (binary search)',
    explanation: 'Binary search is O(log n) — far more efficient than linear O(n) for sorted data.',
    difficulty: 0.45, cognitiveLevel: 2,
  },
  {
    id: 'k5_algo_q3', conceptId: 'k5_algorithms', taskType: 'mpq',
    title: 'Sequence vs. Loop',
    questionText: 'A program must greet 50 different users by name. Which design is best?',
    choices: [
      'Write 50 separate "print name" lines',
      'Use a loop that repeats the greeting for each name in a list',
      'Print all names at once with one print statement',
      'Ask the user to type each name 50 times',
    ],
    correctAnswer: 'Use a loop that repeats the greeting for each name in a list',
    explanation: 'Loops avoid repetitive code — essential for processing collections of data.',
    difficulty: 0.40, cognitiveLevel: 2,
  },

  // ── k8_algorithms ────────────────────────────────────────────────────────
  {
    id: 'k8_algo_q1', conceptId: 'k8_algorithms', taskType: 'mpq',
    title: 'Worst-Case Analysis',
    questionText: 'Algorithm A always takes 100 steps regardless of input size. Algorithm B takes n steps for input size n. For n = 50, which is faster?',
    choices: ['Algorithm A (100 steps vs. 50)', 'Algorithm B (50 steps vs. 100)', 'They are always equal', 'Cannot be determined'],
    correctAnswer: 'Algorithm B (50 steps vs. 100)',
    explanation: 'Algorithm B takes n=50 steps; Algorithm A always takes 100. B is faster for small n but A wins for large n.',
    difficulty: 0.58, cognitiveLevel: 3,
  },
  {
    id: 'k8_algo_q2', conceptId: 'k8_algorithms', taskType: 'mpq',
    title: 'Big-O Intuition',
    questionText: 'A nested loop checks every pair of items in a list of n items. How does the number of operations grow with n?',
    choices: ['Linearly (n)', 'Quadratically (n²)', 'Logarithmically (log n)', 'Constantly (1)'],
    correctAnswer: 'Quadratically (n²)',
    explanation: 'For each of n items the inner loop checks n items: n × n = n² total comparisons.',
    difficulty: 0.65, cognitiveLevel: 3,
  },
  {
    id: 'k8_algo_q3', conceptId: 'k8_algorithms', taskType: 'mpq',
    title: 'Algorithm Correctness',
    questionText: 'An algorithm works perfectly for 999 test cases but fails when the input is empty. What is this called?',
    choices: ['A runtime error', 'An edge case bug', 'A compile error', 'A memory overflow'],
    correctAnswer: 'An edge case bug',
    explanation: 'Edge cases (empty input, maximum values, boundary conditions) must always be explicitly handled.',
    difficulty: 0.62, cognitiveLevel: 3,
  },

  // ── k12_algorithms ────────────────────────────────────────────────────────
  {
    id: 'k12_algo_q1', conceptId: 'k12_algorithms', taskType: 'mpq',
    title: 'Divide and Conquer',
    questionText: 'Merge sort divides a list in half recursively, sorts each half, then merges. What is its time complexity?',
    choices: ['O(n)', 'O(n log n)', 'O(n²)', 'O(log n)'],
    correctAnswer: 'O(n log n)',
    explanation: 'Merge sort makes O(log n) recursive splits and O(n) work per merge level: total O(n log n).',
    difficulty: 0.78, cognitiveLevel: 4,
  },
  {
    id: 'k12_algo_q2', conceptId: 'k12_algorithms', taskType: 'mpq',
    title: 'Dynamic Programming Trade-off',
    questionText: 'Compared to a recursive approach, what does dynamic programming trade to achieve faster computation?',
    choices: ['Less accuracy', 'More memory (to store subproblem results)', 'More code complexity with no speed gain', 'Randomness'],
    correctAnswer: 'More memory (to store subproblem results)',
    explanation: 'DP memoizes (stores) subproblem solutions, trading memory for speed by avoiding redundant computation.',
    difficulty: 0.82, cognitiveLevel: 4,
  },

  // ── k2_control ───────────────────────────────────────────────────────────
  {
    id: 'k2_ctrl_q1', conceptId: 'k2_control', taskType: 'mpq',
    title: 'When to Use a Loop',
    questionText: 'You need to water 10 plants, doing exactly the same action each time. Which is the best approach?',
    choices: [
      'Write 10 separate "water plant" steps',
      'Use a loop that repeats "water plant" 10 times',
      'Water only the first plant',
      'Write a story about watering plants',
    ],
    correctAnswer: 'Use a loop that repeats "water plant" 10 times',
    explanation: 'Loops eliminate repetition for repeated identical actions.',
    difficulty: 0.25, cognitiveLevel: 1,
  },
  {
    id: 'k2_ctrl_q2', conceptId: 'k2_control', taskType: 'mpq',
    title: 'Simple Conditional',
    questionText: 'A program checks: "IF it is raining THEN take an umbrella". What type of instruction is this?',
    choices: ['A loop', 'A conditional (if-then)', 'A variable', 'A function'],
    correctAnswer: 'A conditional (if-then)',
    explanation: 'IF-THEN instructions execute an action only when a condition is true.',
    difficulty: 0.22, cognitiveLevel: 1,
  },
  {
    id: 'k2_ctrl_q3', conceptId: 'k2_control', taskType: 'mpq',
    title: 'Identifying the Loop Body',
    questionText: 'In the instruction "REPEAT 3 TIMES: say hello → wave hand", which steps are inside the loop?',
    choices: [
      'Only "say hello"',
      'Only "wave hand"',
      'Both "say hello" and "wave hand"',
      'Neither — the loop body is empty',
    ],
    correctAnswer: 'Both "say hello" and "wave hand"',
    explanation: 'Everything indented under REPEAT is the loop body — all steps run on every iteration.',
    difficulty: 0.28, cognitiveLevel: 1,
  },

  // ── k5_control ───────────────────────────────────────────────────────────
  {
    id: 'k5_ctrl_q1', conceptId: 'k5_control', taskType: 'mpq',
    title: 'Loop Condition',
    questionText: 'A while loop runs while score < 10. Starting with score = 7, how many times does "score = score + 1" execute?',
    choices: ['7', '3', '10', '1'],
    correctAnswer: '3',
    explanation: 'score goes 7→8→9→10. The loop runs at 7, 8, 9 (3 times), then score = 10 fails the condition.',
    difficulty: 0.45, cognitiveLevel: 2,
  },
  {
    id: 'k5_ctrl_q2', conceptId: 'k5_control', taskType: 'mpq',
    title: 'If-Else Tracing',
    questionText: 'IF score >= 75 THEN print "Pass" ELSE print "Fail". If score = 60, what is printed?',
    choices: ['Pass', 'Fail', 'Nothing', 'Both Pass and Fail'],
    correctAnswer: 'Fail',
    explanation: '60 is not ≥ 75, so the ELSE branch runs: "Fail" is printed.',
    difficulty: 0.42, cognitiveLevel: 2,
  },
  {
    id: 'k5_ctrl_q3', conceptId: 'k5_control', taskType: 'mpq',
    title: 'When to Use For vs While',
    questionText: 'Which loop type is best when you know exactly how many times to repeat?',
    choices: ['While loop', 'For loop', 'Repeat-until loop', 'Recursive function'],
    correctAnswer: 'For loop',
    explanation: 'For loops are designed for a known, fixed number of iterations.',
    difficulty: 0.40, cognitiveLevel: 2,
  },

  // ── k8_control ───────────────────────────────────────────────────────────
  {
    id: 'k8_ctrl_q1', conceptId: 'k8_control', taskType: 'mpq',
    title: 'Nested Loop Work Count',
    questionText: 'An outer loop runs 4 times; an inner loop runs 3 times for each outer iteration. How many total inner loop executions occur?',
    choices: ['7', '12', '4', '3'],
    correctAnswer: '12',
    explanation: '4 × 3 = 12. Nested loops multiply their iteration counts.',
    difficulty: 0.62, cognitiveLevel: 3,
  },
  {
    id: 'k8_ctrl_q2', conceptId: 'k8_control', taskType: 'mpq',
    title: 'Boolean Logic',
    questionText: 'A condition is: (age >= 13) AND (hasPermission = True). For age = 15 and hasPermission = False, what is the result?',
    choices: ['True', 'False', 'Error', 'Depends on the language'],
    correctAnswer: 'False',
    explanation: 'AND requires both conditions to be True. hasPermission is False, so the whole condition is False.',
    difficulty: 0.65, cognitiveLevel: 3,
  },
  {
    id: 'k8_ctrl_q3', conceptId: 'k8_control', taskType: 'mpq',
    title: 'Event-Driven Control',
    questionText: 'In an event-driven program, when does the code inside an "onClick" handler run?',
    choices: [
      'When the program starts',
      'Every second automatically',
      'Only when the user clicks the element',
      'Only when another function calls it',
    ],
    correctAnswer: 'Only when the user clicks the element',
    explanation: 'Event-driven code runs in response to specific user or system events, not continuously.',
    difficulty: 0.60, cognitiveLevel: 3,
  },

  // ── k2_variables ─────────────────────────────────────────────────────────
  {
    id: 'k2_var_q1', conceptId: 'k2_variables', taskType: 'mpq',
    title: 'What is a Variable?',
    questionText: 'In a game, "lives = 3" means the player has 3 lives. If the player loses one, lives becomes 2. What is "lives" in programming?',
    choices: ['A function', 'A variable that stores a changing value', 'A fixed number that never changes', 'A type of loop'],
    correctAnswer: 'A variable that stores a changing value',
    explanation: 'Variables are named storage containers whose values can change during program execution.',
    difficulty: 0.20, cognitiveLevel: 1,
  },
  {
    id: 'k2_var_q2', conceptId: 'k2_variables', taskType: 'mpq',
    title: 'Assignment Direction',
    questionText: 'x = 5 means what in programming?',
    choices: [
      '"x" equals 5 like in math — both sides are equal',
      '"Store the value 5 in the variable named x"',
      '"Check if x and 5 are equal"',
      '"Multiply x by 5"',
    ],
    correctAnswer: '"Store the value 5 in the variable named x"',
    explanation: 'Assignment (=) stores a value. It is directional: value goes INTO the variable.',
    difficulty: 0.22, cognitiveLevel: 1,
  },

  // ── k5_variables ─────────────────────────────────────────────────────────
  {
    id: 'k5_var_q1', conceptId: 'k5_variables', taskType: 'mpq',
    title: 'Data Types',
    questionText: 'Which is the correct data type for storing a student\'s average score like 85.5?',
    choices: ['Integer (whole number)', 'Float (decimal number)', 'Boolean (true/false)', 'String (text)'],
    correctAnswer: 'Float (decimal number)',
    explanation: 'Floats (or doubles) represent numbers with decimal points. 85.5 cannot be stored as an integer.',
    difficulty: 0.38, cognitiveLevel: 2,
  },
  {
    id: 'k5_var_q2', conceptId: 'k5_variables', taskType: 'mpq',
    title: 'Variable Reassignment',
    questionText: 'x = 10; x = x + 3; print(x). What is printed?',
    choices: ['10', '3', '13', 'x + 3'],
    correctAnswer: '13',
    explanation: 'x starts as 10. x = x + 3 computes 10 + 3 = 13 and stores it back in x.',
    difficulty: 0.40, cognitiveLevel: 2,
  },

  // ── k8_variables ─────────────────────────────────────────────────────────
  {
    id: 'k8_var_q1', conceptId: 'k8_variables', taskType: 'mpq',
    title: 'Local vs Global Scope',
    questionText: 'A variable declared inside a function is called what, and where can it be accessed?',
    choices: [
      'A global variable — accessible everywhere',
      'A local variable — accessible only inside that function',
      'A constant — its value never changes',
      'A parameter — only passed in function calls',
    ],
    correctAnswer: 'A local variable — accessible only inside that function',
    explanation: 'Local variables are scoped to the block (function) where they are declared.',
    difficulty: 0.58, cognitiveLevel: 3,
  },
  {
    id: 'k8_var_q2', conceptId: 'k8_variables', taskType: 'mpq',
    title: 'List Indexing',
    questionText: 'names = ["Adi", "Budi", "Citra"]. What is names[1]?',
    choices: ['Adi', 'Budi', 'Citra', 'Index error'],
    correctAnswer: 'Budi',
    explanation: 'List indexing starts at 0. Index 1 gives the second element: "Budi".',
    difficulty: 0.55, cognitiveLevel: 2,
  },

  // ── k2_modularity ────────────────────────────────────────────────────────
  {
    id: 'k2_mod_q1', conceptId: 'k2_modularity', taskType: 'mpq',
    title: 'Breaking Down Problems',
    questionText: 'To clean your room you must: tidy desk, organize books, sweep floor. This is an example of:',
    choices: ['Compiling code', 'Decomposition — breaking a big task into smaller steps', 'A network protocol', 'A variable'],
    correctAnswer: 'Decomposition — breaking a big task into smaller steps',
    explanation: 'Decomposition is a key computational thinking skill: divide large problems into manageable sub-problems.',
    difficulty: 0.22, cognitiveLevel: 1,
  },
  {
    id: 'k2_mod_q2', conceptId: 'k2_modularity', taskType: 'mpq',
    title: 'Reuse',
    questionText: 'You teach a robot to "wave hello". Later you use "wave hello" 5 times without rewriting the steps. What concept is this?',
    choices: ['Reusing a named procedure', 'A loop', 'A conditional', 'Data storage'],
    correctAnswer: 'Reusing a named procedure',
    explanation: 'Defining a named procedure once and reusing it is the foundation of modularity.',
    difficulty: 0.25, cognitiveLevel: 1,
  },

  // ── k5_modularity ────────────────────────────────────────────────────────
  {
    id: 'k5_mod_q1', conceptId: 'k5_modularity', taskType: 'mpq',
    title: 'Function with Parameters',
    questionText: 'def greet(name): print("Hello", name). When you call greet("Siti"), what is printed?',
    choices: ['Hello name', 'Hello Siti', 'Hello', 'Error'],
    correctAnswer: 'Hello Siti',
    explanation: 'The parameter "name" receives the value "Siti" when the function is called.',
    difficulty: 0.42, cognitiveLevel: 2,
  },
  {
    id: 'k5_mod_q2', conceptId: 'k5_modularity', taskType: 'mpq',
    title: 'Return Values',
    questionText: 'def square(n): return n * n. What does square(4) evaluate to?',
    choices: ['4', '8', '16', 'n*n'],
    correctAnswer: '16',
    explanation: 'The function returns n*n = 4*4 = 16. Return values allow functions to produce results.',
    difficulty: 0.45, cognitiveLevel: 2,
  },

  // ── k8_modularity ────────────────────────────────────────────────────────
  {
    id: 'k8_mod_q1', conceptId: 'k8_modularity', taskType: 'mpq',
    title: 'Why Use Functions',
    questionText: 'Your program has identical code in three different places. What is the best refactoring approach?',
    choices: [
      'Keep three copies — it\'s clearer',
      'Extract the code into a single function and call it from each place',
      'Delete two copies and keep one',
      'Add comments explaining the duplication',
    ],
    correctAnswer: 'Extract the code into a single function and call it from each place',
    explanation: 'DRY (Don\'t Repeat Yourself): centralising code reduces bugs and maintenance cost.',
    difficulty: 0.60, cognitiveLevel: 3,
  },

  // ── k2_computing_systems_devices ─────────────────────────────────────────
  {
    id: 'k2_cs_q1', conceptId: 'k2_computing_systems_devices', taskType: 'mpq',
    title: 'Hardware vs Software',
    questionText: 'Which of these is an example of software?',
    choices: ['The keyboard you type on', 'The screen you look at', 'A calculator application on a phone', 'The USB cable you plug in'],
    correctAnswer: 'A calculator application on a phone',
    explanation: 'Software is a program — instructions stored digitally. Hardware is physical.',
    difficulty: 0.20, cognitiveLevel: 1,
  },
  {
    id: 'k2_cs_q2', conceptId: 'k2_computing_systems_devices', taskType: 'mpq',
    title: 'Input and Output',
    questionText: 'When you press a key on the keyboard, it sends information to the computer. The keyboard is a:',
    choices: ['Output device', 'Input device', 'Storage device', 'Processing unit'],
    correctAnswer: 'Input device',
    explanation: 'Input devices send data to the computer. Output devices (like monitors) receive data from it.',
    difficulty: 0.18, cognitiveLevel: 1,
  },

  // ── k5_computing_systems_devices ─────────────────────────────────────────
  {
    id: 'k5_cs_q1', conceptId: 'k5_computing_systems_devices', taskType: 'mpq',
    title: 'Role of the CPU',
    questionText: 'What is the primary function of the CPU (Central Processing Unit)?',
    choices: [
      'Store files permanently',
      'Display images on screen',
      'Execute program instructions — the "brain" of the computer',
      'Connect the computer to the internet',
    ],
    correctAnswer: 'Execute program instructions — the "brain" of the computer',
    explanation: 'The CPU fetches, decodes, and executes instructions — it is the computational core.',
    difficulty: 0.40, cognitiveLevel: 2,
  },
  {
    id: 'k5_cs_q2', conceptId: 'k5_computing_systems_devices', taskType: 'mpq',
    title: 'RAM vs Storage',
    questionText: 'When you close a document without saving, the work is lost. This is because it was only in:',
    choices: ['The hard drive (permanent storage)', 'RAM (temporary memory)', 'The CPU cache', 'The graphics card'],
    correctAnswer: 'RAM (temporary memory)',
    explanation: 'RAM is volatile — it loses data when power is off. Permanent storage (SSD/HDD) keeps data.',
    difficulty: 0.42, cognitiveLevel: 2,
  },

  // ── k8_computing_systems_devices ─────────────────────────────────────────
  {
    id: 'k8_cs_q1', conceptId: 'k8_computing_systems_devices', taskType: 'mpq',
    title: 'Operating System Role',
    questionText: 'Which task does the operating system NOT perform?',
    choices: [
      'Managing memory allocation between programs',
      'Controlling hardware devices via drivers',
      'Executing the CPU\'s fetch-decode-execute cycle',
      'Managing the file system and storage',
    ],
    correctAnswer: 'Executing the CPU\'s fetch-decode-execute cycle',
    explanation: 'The OS manages resources, but the fetch-decode-execute cycle is performed by the CPU hardware itself.',
    difficulty: 0.62, cognitiveLevel: 3,
  },

  // ── k2_networks_communication ─────────────────────────────────────────────
  {
    id: 'k2_net_q1', conceptId: 'k2_networks_communication', taskType: 'mpq',
    title: 'What is a Network?',
    questionText: 'Three computers in a classroom are connected so they can share files. What is this called?',
    choices: ['A database', 'A loop', 'A computer network', 'An operating system'],
    correctAnswer: 'A computer network',
    explanation: 'A network is two or more connected devices that can communicate and share resources.',
    difficulty: 0.20, cognitiveLevel: 1,
  },
  {
    id: 'k2_net_q2', conceptId: 'k2_networks_communication', taskType: 'mpq',
    title: 'Internet Basics',
    questionText: 'When you visit a website, your computer communicates with another computer far away. What makes this possible?',
    choices: [
      'The keyboard sends the request directly',
      'The internet connects computers worldwide so they can exchange data',
      'The screen downloads the website',
      'The RAM stores websites permanently',
    ],
    correctAnswer: 'The internet connects computers worldwide so they can exchange data',
    explanation: 'The internet is a global network of networks enabling worldwide data communication.',
    difficulty: 0.22, cognitiveLevel: 1,
  },

  // ── k5_networks_communication ─────────────────────────────────────────────
  {
    id: 'k5_net_q1', conceptId: 'k5_networks_communication', taskType: 'mpq',
    title: 'What is a Protocol?',
    questionText: 'HTTP is a set of rules that web browsers and servers follow to share web pages. HTTP is an example of:',
    choices: ['A programming language', 'A network protocol', 'A database', 'A hardware component'],
    correctAnswer: 'A network protocol',
    explanation: 'Protocols are agreed-upon rules for communication. HTTP defines how web data is requested and served.',
    difficulty: 0.40, cognitiveLevel: 2,
  },
  {
    id: 'k5_net_q2', conceptId: 'k5_networks_communication', taskType: 'mpq',
    title: 'Packets',
    questionText: 'Why does the internet break large files into small "packets" before sending?',
    choices: [
      'Because packets are harder to hack',
      'To allow efficient routing — each packet can take a different path',
      'Because computers cannot handle large files',
      'To compress files automatically',
    ],
    correctAnswer: 'To allow efficient routing — each packet can take a different path',
    explanation: 'Packet switching allows efficient use of network paths and resilience to failures.',
    difficulty: 0.45, cognitiveLevel: 2,
  },

  // ── k8_networks_communication ─────────────────────────────────────────────
  {
    id: 'k8_net_q1', conceptId: 'k8_networks_communication', taskType: 'mpq',
    title: 'IP Address',
    questionText: 'An IP address like 192.168.1.5 uniquely identifies a device on a network. What does the IP address enable?',
    choices: [
      'Encrypting messages so they cannot be read',
      'Routing data packets to the correct destination device',
      'Storing web pages on the device',
      'Speeding up the CPU',
    ],
    correctAnswer: 'Routing data packets to the correct destination device',
    explanation: 'IP addresses are used by routers to direct packets to the correct machine on the network.',
    difficulty: 0.58, cognitiveLevel: 3,
  },
  {
    id: 'k8_net_q2', conceptId: 'k8_networks_communication', taskType: 'mpq',
    title: 'Cybersecurity Basics',
    questionText: 'A hacker sends an email pretending to be your bank, asking for your password. This is called:',
    choices: ['A denial of service attack', 'Phishing', 'Malware', 'Packet sniffing'],
    correctAnswer: 'Phishing',
    explanation: 'Phishing uses fake messages that impersonate trusted sources to steal credentials.',
    difficulty: 0.55, cognitiveLevel: 2,
  },

  // ── k2_data_collection ───────────────────────────────────────────────────
  {
    id: 'k2_data_q1', conceptId: 'k2_data_collection', taskType: 'mpq',
    title: 'Collecting Data',
    questionText: 'Your class wants to find out which fruit is most popular. How should you collect data?',
    choices: [
      'Ask one student and guess the rest',
      'Ask every student their favourite fruit and record the answers',
      'Choose the fruit you like most',
      'Look it up on the internet',
    ],
    correctAnswer: 'Ask every student their favourite fruit and record the answers',
    explanation: 'Good data collection means gathering responses from all relevant subjects systematically.',
    difficulty: 0.18, cognitiveLevel: 1,
  },
  {
    id: 'k2_data_q2', conceptId: 'k2_data_collection', taskType: 'mpq',
    title: 'Reading a Chart',
    questionText: 'A bar chart shows: Mango = 8, Banana = 5, Apple = 3. Which fruit is most popular?',
    choices: ['Apple', 'Banana', 'Mango', 'They are all equal'],
    correctAnswer: 'Mango',
    explanation: 'Mango has the tallest bar (8 students), so it is the most popular.',
    difficulty: 0.18, cognitiveLevel: 1,
  },

  // ── k5_data_collection ───────────────────────────────────────────────────
  {
    id: 'k5_data_q1', conceptId: 'k5_data_collection', taskType: 'mpq',
    title: 'Patterns in Data',
    questionText: 'Temperature readings for 7 days: 28, 30, 29, 31, 30, 32, 31. What is the trend?',
    choices: ['Temperature is falling', 'Temperature is roughly rising', 'Temperature is constant', 'No pattern exists'],
    correctAnswer: 'Temperature is roughly rising',
    explanation: 'Despite daily fluctuations, the overall sequence moves from 28 to 31 — an upward trend.',
    difficulty: 0.40, cognitiveLevel: 2,
  },
  {
    id: 'k5_data_q2', conceptId: 'k5_data_collection', taskType: 'mpq',
    title: 'Correlation vs Causation',
    questionText: 'Data shows that students who eat breakfast score higher on tests. What can we conclude?',
    choices: [
      'Eating breakfast directly causes higher scores',
      'There is a correlation, but we need more evidence to prove causation',
      'Test scores cause students to eat breakfast',
      'The data must be wrong',
    ],
    correctAnswer: 'There is a correlation, but we need more evidence to prove causation',
    explanation: 'Correlation means two things move together. Causation requires controlled experiments to confirm.',
    difficulty: 0.48, cognitiveLevel: 2,
  },

  // ── k8_data_collection ───────────────────────────────────────────────────
  {
    id: 'k8_data_q1', conceptId: 'k8_data_collection', taskType: 'mpq',
    title: 'Sampling Bias',
    questionText: 'A survey asks only students in the computer lab about technology use. What is wrong with this sample?',
    choices: [
      'The sample is too small',
      'It is biased — computer lab students are more tech-oriented than the general population',
      'Online surveys are never valid',
      'Nothing is wrong — any sample is acceptable',
    ],
    correctAnswer: 'It is biased — computer lab students are more tech-oriented than the general population',
    explanation: 'Sampling bias occurs when the sample does not represent the target population.',
    difficulty: 0.58, cognitiveLevel: 3,
  },

  // ── k12_data_collection ──────────────────────────────────────────────────
  {
    id: 'k12_data_q1', conceptId: 'k12_data_collection', taskType: 'mpq',
    title: 'Training vs Test Sets',
    questionText: 'Why do machine learning practitioners hold out a "test set" that the model never sees during training?',
    choices: [
      'To save computation time',
      'To measure how well the model generalises to unseen data',
      'Because the test set is always smaller than the training set',
      'To make the model simpler',
    ],
    correctAnswer: 'To measure how well the model generalises to unseen data',
    explanation: 'If the model is evaluated on training data, it may just memorise (overfit). A held-out test set reveals true generalisation.',
    difficulty: 0.78, cognitiveLevel: 4,
  },

  // ── k2_culture ──────────────────────────────────────────────────────────
  {
    id: 'k2_dsi_q1', conceptId: 'k2_culture', taskType: 'mpq',
    title: 'Technology in Daily Life',
    questionText: 'Smartphones help people communicate quickly, but some people use them too much and ignore those around them. This shows technology can have:',
    choices: [
      'Only positive effects',
      'Only negative effects',
      'Both positive and negative effects depending on how it is used',
      'No effect on daily life',
    ],
    correctAnswer: 'Both positive and negative effects depending on how it is used',
    explanation: 'Technology is a tool — its impact depends on how, when, and how much it is used.',
    difficulty: 0.18, cognitiveLevel: 1,
  },
  {
    id: 'k2_dsi_q2', conceptId: 'k2_culture', taskType: 'mpq',
    title: 'Online Safety',
    questionText: 'Your friend asks you to share your home address on a public social media post. What should you do?',
    choices: [
      'Share it because you trust your friend',
      'Refuse — personal information like addresses should not be shared publicly',
      'Share only half the address',
      'Ask an adult after posting',
    ],
    correctAnswer: 'Refuse — personal information like addresses should not be shared publicly',
    explanation: 'Personal information shared publicly can be seen by strangers and misused.',
    difficulty: 0.20, cognitiveLevel: 1,
  },

  // ── k5_culture ──────────────────────────────────────────────────────────
  {
    id: 'k5_dsi_q1', conceptId: 'k5_culture', taskType: 'mpq',
    title: 'Digital Citizenship',
    questionText: 'Copying someone else\'s paragraph from the internet and submitting it as your own is:',
    choices: ['Efficient research', 'Plagiarism — using others\' work without credit', 'Legal if you change a few words', 'Acceptable for school work'],
    correctAnswer: 'Plagiarism — using others\' work without credit',
    explanation: 'Intellectual property rights apply online. Copying without attribution is plagiarism.',
    difficulty: 0.38, cognitiveLevel: 2,
  },

  // ── k8_culture ──────────────────────────────────────────────────────────
  {
    id: 'k8_dsi_q1', conceptId: 'k8_culture', taskType: 'mpq',
    title: 'Algorithmic Bias',
    questionText: 'A hiring algorithm trained mostly on male engineers consistently rates female candidates lower. This is an example of:',
    choices: [
      'Correct and efficient AI',
      'Algorithmic bias caused by biased training data',
      'A bug in the server hardware',
      'Normal variation in candidate quality',
    ],
    correctAnswer: 'Algorithmic bias caused by biased training data',
    explanation: 'When training data reflects historical bias, algorithms learn and amplify that bias — a key AI ethics issue.',
    difficulty: 0.62, cognitiveLevel: 3,
  },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** All unique concept IDs in the catalog */
export const ALL_CONCEPT_IDS = K12_CONCEPTS.map(c => c.id)

/** Look up a concept by ID */
export function getConcept(id: string): K12Concept | undefined {
  return K12_CONCEPTS.find(c => c.id === id)
}

/** Human-readable label for a concept ID */
export function conceptLabel(id: string): string {
  const c = getConcept(id)
  if (c) return c.label
  // Fallback: prettify the ID
  return id
    .replace(/^(k2|k5|k8|k12)_/, (m, band) => `${band.toUpperCase()}: `)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
}

/** Get all tasks for a concept, optionally filtered by task type */
export function getTasksForConcept(conceptId: string, taskType?: string): K12Task[] {
  return K12_TASKS.filter(t =>
    t.conceptId === conceptId && (!taskType || t.taskType === taskType)
  )
}

/** Get a random task for a concept (used in offline/demo mode) */
export function pickTask(conceptId: string, seed?: number): K12Task | null {
  const tasks = getTasksForConcept(conceptId)
  if (tasks.length === 0) return null
  const idx = seed != null ? seed % tasks.length : Math.floor(Math.random() * tasks.length)
  return tasks[idx]
}

/** Grade band ordering for progression logic */
const BAND_ORDER: GradeBand[] = ['K-2', 'K-5', 'K-8', 'K-12']

/**
 * Suggest next concept to study given current mastery map.
 * Strategy: find the lowest-mastery concept that has all prerequisites mastered.
 */
export function suggestNextConcept(
  masteryMap: Record<string, number>,
  masteryThreshold = 0.7
): K12Concept | null {
  const mastered = new Set(
    Object.entries(masteryMap)
      .filter(([, m]) => m >= masteryThreshold)
      .map(([id]) => id)
  )

  // Candidates: prereqs all mastered, concept not yet mastered
  const candidates = K12_CONCEPTS.filter(c => {
    const currentMastery = masteryMap[c.id] ?? 0
    if (currentMastery >= masteryThreshold) return false // already mastered
    return c.prerequisites.every(p => mastered.has(p))
  })

  if (candidates.length === 0) return null

  // Sort by: lowest mastery first, then lowest difficulty
  candidates.sort((a, b) => {
    const ma = masteryMap[a.id] ?? 0
    const mb = masteryMap[b.id] ?? 0
    if (Math.abs(ma - mb) > 0.05) return ma - mb
    return a.difficulty - b.difficulty
  })

  return candidates[0]
}

/**
 * Build a mock mastery map for demo/offline mode.
 * Simulates a learner who has progressed through K-2 concepts
 * and is mid-way through K-5.
 */
export function buildDemoMasteryMap(): Record<string, number> {
  const map: Record<string, number> = {}
  for (const c of K12_CONCEPTS) {
    const band = c.gradeBand
    if (band === 'K-2') {
      map[c.id] = 0.65 + Math.random() * 0.25   // mostly mastered
    } else if (band === 'K-5') {
      map[c.id] = 0.30 + Math.random() * 0.35   // in progress
    } else if (band === 'K-8') {
      map[c.id] = 0.05 + Math.random() * 0.15   // just started
    } else {
      map[c.id] = 0                               // not yet reached
    }
  }
  return map
}

/**
 * Build a mock JT trajectory (learning history) for demo mode.
 */
export function buildDemoTrajectory(steps = 30): Array<{
  step: number
  conceptId: string
  jt: number
  delta_m: number
  transfer_realized: number
  correct: boolean
}> {
  const conceptIds = K12_CONCEPTS
    .filter(c => c.gradeBand === 'K-2' || c.gradeBand === 'K-5')
    .map(c => c.id)

  return Array.from({ length: steps }, (_, i) => {
    const correct = Math.random() > 0.35
    const jt = Math.max(0, Math.min(1,
      0.35 + (i / steps) * 0.4 + (Math.random() - 0.5) * 0.1
    ))
    return {
      step: i + 1,
      conceptId: conceptIds[i % conceptIds.length],
      jt,
      delta_m: correct ? 0.02 + Math.random() * 0.04 : -0.005 - Math.random() * 0.01,
      transfer_realized: (i % 5 === 0 && correct) ? 0.12 + Math.random() * 0.10 : 0.01,
      correct,
    }
  })
}
