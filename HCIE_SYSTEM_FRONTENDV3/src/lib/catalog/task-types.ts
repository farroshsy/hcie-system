/**
 * task-types.ts — Multi-format task model for the ITS.
 *
 * The platform's MAB selects a *modality* per interaction; this module turns that
 * selection into a concrete, interactive task whose FORMAT is matched to a Bloom
 * level and an Indonesian Informatika curriculum strand. Each kind also declares
 * the signal it captures, so an attempt carries more than a binary correct/wrong.
 *
 * Design table (kind · Bloom verb · strand fit · captured signal):
 *   mcq                 recognize          any                binary correct/incorrect
 *   trace               comprehend         AP                 predicted vs expected, steps viewed
 *   parsons             comprehend + order AP                 block order, indent, distractors
 *   code_write          produce (text)     AP                 test-pass vector
 *   block_program       produce (visual)   AP                 structure flags (loop/branch/order)
 *   case_study          evaluate           DSI · DA · JKI     decision + reasoning path
 *   data_interpretation interpret          SK · DA            answer derived from the data
 *   diagram_label       interpret          JKI                labels assigned to diagram parts
 */

// ─── Strands (Indonesian Informatika / "Capaian Pembelajaran") ─────────────────
export type Strand = 'AP' | 'SK' | 'JKI' | 'DA' | 'DSI' | 'any'

export const STRAND_LABEL: Record<Strand, string> = {
  AP:  'Algoritma & Pemrograman',      // Algorithms & Programming
  SK:  'Sistem Komputer',              // Computer Systems
  JKI: 'Jaringan Komputer & Internet', // Networks & Internet
  DA:  'Analisis Data',                // Data Analysis
  DSI: 'Dampak Sosial Informatika',    // Social Impact of Informatics
  any: 'Any strand',
}

// Map a catalog ConceptArea (k12-catalog) onto a strand, so a recommended concept
// can pick a format whose strand fit matches.
export function strandForConceptArea(area: string): Strand {
  switch (area) {
    case 'Algorithms':
    case 'Control Structures':
    case 'Variables':
    case 'Modularity':
    case 'Program Development': return 'AP'
    case 'Computing Systems':   return 'SK'
    case 'Networks':            return 'JKI'
    case 'Data Analysis':       return 'DA'
    case 'Social Impacts':      return 'DSI'
    default:                    return 'any'
  }
}

// ─── Bloom ─────────────────────────────────────────────────────────────────────
export type BloomLevel = 1 | 2 | 3 | 4 | 5 | 6
export const BLOOM_LABEL: Record<BloomLevel, string> = {
  1: 'Remember', 2: 'Understand', 3: 'Apply', 4: 'Analyze', 5: 'Evaluate', 6: 'Create',
}

// ─── Task kinds + per-kind metadata ────────────────────────────────────────────
export type TaskKind =
  | 'mcq'
  | 'trace'
  | 'parsons'
  | 'code_write'
  | 'block_program'
  | 'case_study'
  | 'data_interpretation'
  | 'diagram_label'
  | 'video_question'
  | 'audio_listen'

export interface TaskKindMeta {
  kind: TaskKind
  label: string
  bloom: BloomLevel
  bloomVerb: string      // the curriculum's verb, e.g. "comprehend", "produce (text)"
  strands: Strand[]      // strand fit from the design table
  signal: string         // human description of the captured signal
  signalKeys: string[]   // keys present in TaskSignal.detail
  icon: string
  color: string
  desc: string           // one-line instruction shown to the learner
}

export const TASK_KIND_META: Record<TaskKind, TaskKindMeta> = {
  mcq: {
    kind: 'mcq', label: 'Multiple Choice', bloom: 1, bloomVerb: 'recognize', strands: ['any'],
    signal: 'binary correct / incorrect', signalKeys: ['correct'],
    icon: '◉', color: '#2980B9', desc: 'Select the best answer',
  },
  trace: {
    kind: 'trace', label: 'Code Trace', bloom: 2, bloomVerb: 'comprehend', strands: ['AP'],
    signal: 'predicted vs expected output, steps viewed', signalKeys: ['predicted', 'expected', 'stepsViewed'],
    icon: '⊳', color: '#8E44AD', desc: 'Predict what the code prints',
  },
  parsons: {
    kind: 'parsons', label: 'Parsons Problem', bloom: 2, bloomVerb: 'comprehend + order', strands: ['AP'],
    signal: 'block order, indentation, distractors kept', signalKeys: ['order', 'indents', 'distractorsUsed'],
    icon: '⇅', color: '#16A085', desc: 'Arrange the blocks into a correct program',
  },
  code_write: {
    kind: 'code_write', label: 'Write Code', bloom: 3, bloomVerb: 'produce (text)', strands: ['AP'],
    signal: 'test-pass vector', signalKeys: ['code', 'testsPassed'],
    icon: '⌨', color: '#2C3E50', desc: 'Write code that passes every test',
  },
  block_program: {
    kind: 'block_program', label: 'Block Program', bloom: 3, bloomVerb: 'produce (visual)', strands: ['AP'],
    signal: 'structure flags (loop / branch / order)', signalKeys: ['sequence', 'structureFlags'],
    icon: '▦', color: '#D35400', desc: 'Build the program from blocks',
  },
  case_study: {
    kind: 'case_study', label: 'Case Study', bloom: 5, bloomVerb: 'evaluate', strands: ['DSI', 'DA', 'JKI'],
    signal: 'decision + reasoning path', signalKeys: ['decision', 'reasoning', 'sound'],
    icon: '⚖', color: '#C0392B', desc: 'Make a decision and justify it',
  },
  data_interpretation: {
    kind: 'data_interpretation', label: 'Data Interpretation', bloom: 4, bloomVerb: 'interpret', strands: ['SK', 'DA'],
    signal: 'answer derived from the data', signalKeys: ['answer'],
    icon: '▤', color: '#1F618D', desc: 'Read the data and answer',
  },
  diagram_label: {
    kind: 'diagram_label', label: 'Diagram Labeling', bloom: 4, bloomVerb: 'interpret', strands: ['JKI'],
    signal: 'labels assigned to diagram parts', signalKeys: ['labels'],
    icon: '⬡', color: '#117A65', desc: 'Label each part of the diagram',
  },
  video_question: {
    kind: 'video_question', label: 'Video Checkpoint', bloom: 2, bloomVerb: 'understand', strands: ['any'],
    signal: 'answer after video, media engagement', signalKeys: ['correct', 'mediaProgress'],
    icon: '▶', color: '#C0392B', desc: 'Watch, then answer',
  },
  audio_listen: {
    kind: 'audio_listen', label: 'Audio Checkpoint', bloom: 2, bloomVerb: 'understand', strands: ['any'],
    signal: 'answer after listening, media engagement', signalKeys: ['correct', 'mediaProgress'],
    icon: '♪', color: '#6C3483', desc: 'Listen, then answer',
  },
}

// ─── Per-kind content shapes (discriminated by `kind`) ──────────────────────────
interface BaseTask {
  id: string
  conceptId: string
  strand: Strand
  difficulty: number          // 0–1
  title: string
  prompt: string
}

export interface McqTask extends BaseTask {
  kind: 'mcq'
  choices: string[]
  correctIndex: number
  explanation?: string
}
export interface TraceTask extends BaseTask {
  kind: 'trace'
  code: string                // shown read-only
  steps: string[]             // revealable trace walk; each reveal counts
  expectedOutput: string
  outputChoices?: string[]    // if present, answer by choice; else free text
}
export interface ParsonsBlock { id: string; text: string; indent: number }
export interface ParsonsTask extends BaseTask {
  kind: 'parsons'
  blocks: ParsonsBlock[]      // in CORRECT order + indent
  distractors?: { id: string; text: string }[]  // must be removed
}
export interface CodeTest { name: string; mustInclude: string[] } // token heuristic (demo grader)
export interface CodeWriteTask extends BaseTask {
  kind: 'code_write'
  starter: string
  tests: CodeTest[]
  sampleSolution?: string
}
export interface BlockProgramTask extends BaseTask {
  kind: 'block_program'
  palette: string[]           // available blocks (may repeat-use)
  target: string[]            // correct sequence
  goal: string
}
export interface CaseOption { id: string; text: string; sound: boolean }
export interface CaseStudyTask extends BaseTask {
  kind: 'case_study'
  scenario: string
  options: CaseOption[]
  correctId: string
  reasoningPrompt: string
}
export interface DataInterpTask extends BaseTask {
  kind: 'data_interpretation'
  table: { headers: string[]; rows: string[][] }
  choices: string[]
  correctIndex: number
}
export interface DiagramSlot { id: string; x: number; y: number; answer: string }
export interface DiagramLabelTask extends BaseTask {
  kind: 'diagram_label'
  diagram: 'network' | 'system'
  slots: DiagramSlot[]
  bank: string[]
}
export interface VideoQuestionTask extends BaseTask {
  kind: 'video_question'
  mediaUrl: string
  transcript?: string
  choices: string[]
  correctIndex: number
  explanation?: string
}
export interface AudioListenTask extends BaseTask {
  kind: 'audio_listen'
  mediaUrl: string
  transcript?: string
  choices: string[]
  correctIndex: number
  explanation?: string
}

export type DemoTask =
  | McqTask | TraceTask | ParsonsTask | CodeWriteTask
  | BlockProgramTask | CaseStudyTask | DataInterpTask | DiagramLabelTask
  | VideoQuestionTask | AudioListenTask

// ─── The signal a renderer emits back to the page ───────────────────────────────
export interface TaskSignal {
  kind: TaskKind
  answer: string                  // canonical answer string posted to the backend
  correct: boolean | null         // client-graded (these demo tasks know their answer)
  complete: boolean               // enough input to allow Submit
  detail: Record<string, any>     // the kind-specific signal (the "Signal" column)
}

// ─── Task pool — one rich example per kind, concept-tied, strand-spread ──────────
export const DEMO_TASK_POOL: DemoTask[] = [
  // ── recognize / any ──────────────────────────────────────────────────────────
  {
    kind: 'mcq', id: 'mcq_k5_algo_loopsum', conceptId: 'k5_algorithms', strand: 'AP',
    difficulty: 0.38, title: 'Loop accumulation',
    prompt: 'A loop runs "add 2 to total" exactly 5 times, starting at total = 0. What is the final value of total?',
    choices: ['5', '7', '10', '2'], correctIndex: 2,
    explanation: '2 added 5 times = 10.',
  },
  // ── comprehend / AP ──────────────────────────────────────────────────────────
  {
    kind: 'trace', id: 'trace_k8_ctrl_evenodd', conceptId: 'k8_control', strand: 'AP',
    difficulty: 0.55, title: 'Trace a loop with a branch',
    prompt: 'Read the program and predict exactly what it prints.',
    code: [
      'total = 0',
      'for n in [1, 2, 3, 4]:',
      '    if n % 2 == 0:',
      '        total = total + n',
      'print(total)',
    ].join('\n'),
    steps: [
      'n = 1 → 1 % 2 == 1, odd → skip',
      'n = 2 → even → total = 0 + 2 = 2',
      'n = 3 → odd → skip',
      'n = 4 → even → total = 2 + 4 = 6',
      'print(total) → 6',
    ],
    expectedOutput: '6',
    outputChoices: ['4', '6', '10', '2'],
  },
  // ── comprehend + order / AP ──────────────────────────────────────────────────
  {
    kind: 'parsons', id: 'parsons_k8_algo_maxlist', conceptId: 'k8_algorithms', strand: 'AP',
    difficulty: 0.6, title: 'Order the "find maximum" algorithm',
    prompt: 'Arrange the blocks so the program finds the largest number in a list. Remove any block that does not belong.',
    blocks: [
      { id: 'b1', text: 'largest = numbers[0]', indent: 0 },
      { id: 'b2', text: 'for n in numbers:', indent: 0 },
      { id: 'b3', text: 'if n > largest:', indent: 1 },
      { id: 'b4', text: 'largest = n', indent: 2 },
      { id: 'b5', text: 'print(largest)', indent: 0 },
    ],
    distractors: [
      { id: 'd1', text: 'largest = 0' },
    ],
  },
  // ── produce (text) / AP ──────────────────────────────────────────────────────
  {
    kind: 'code_write', id: 'code_k12_algo_sum', conceptId: 'k12_algorithms', strand: 'AP',
    difficulty: 0.72, title: 'Write a sum function',
    prompt: 'Write a function total(numbers) that returns the sum of a list using a loop. The tests check for a function definition, a loop, an accumulator, and a return.',
    starter: 'def total(numbers):\n    # your code here\n    ',
    tests: [
      { name: 'defines total()', mustInclude: ['def total'] },
      { name: 'uses a loop',     mustInclude: ['for'] },
      { name: 'accumulates',     mustInclude: ['+'] },
      { name: 'returns a value', mustInclude: ['return'] },
    ],
    sampleSolution: 'def total(numbers):\n    s = 0\n    for n in numbers:\n        s = s + n\n    return s',
  },
  // ── produce (visual) / AP ────────────────────────────────────────────────────
  {
    kind: 'block_program', id: 'block_k2_algo_square', conceptId: 'k2_algorithms', strand: 'AP',
    difficulty: 0.28, title: 'Make the robot draw a square',
    goal: 'Drive the robot in a square: move and turn the right number of times. Tip: a loop is shorter than four copies.',
    palette: ['move forward', 'turn right', 'repeat 4 times', 'end repeat'],
    target: ['repeat 4 times', 'move forward', 'turn right', 'end repeat'],
    prompt: 'Build the shortest block program that draws a square.',
  },
  // ── evaluate / DSI ───────────────────────────────────────────────────────────
  {
    kind: 'case_study', id: 'case_k8_dsi_privacy', conceptId: 'k8_culture', strand: 'DSI',
    difficulty: 0.66, title: 'A free app wants your contacts',
    prompt: 'Read the situation, choose the most responsible action, and justify it.',
    scenario: 'A free game asks for permission to read your entire contact list and upload it "to find friends". The game does not need contacts to run. Your classmates have already installed it.',
    options: [
      { id: 'o1', text: 'Allow it — everyone else did, so it must be safe.', sound: false },
      { id: 'o2', text: 'Deny the contacts permission and still play the game.', sound: true },
      { id: 'o3', text: 'Allow it once, then uninstall later if something feels wrong.', sound: false },
    ],
    correctId: 'o2',
    reasoningPrompt: 'In one sentence, explain why your choice best protects other people\'s data, not just your own.',
  },
  // ── interpret / SK · DA ──────────────────────────────────────────────────────
  {
    kind: 'data_interpretation', id: 'data_k8_sk_usage', conceptId: 'k8_computing_systems_devices', strand: 'SK',
    difficulty: 0.5, title: 'Which process should you close?',
    prompt: 'A laptop is slow. The table shows running processes. Which one is the best candidate to close to free the most memory while keeping the system usable?',
    table: {
      headers: ['Process', 'CPU %', 'Memory (MB)', 'Needed to run the OS?'],
      rows: [
        ['system',        '4',  '120',  'yes'],
        ['browser (12 tabs)', '9', '1850', 'no'],
        ['music player',  '2',  '180',  'no'],
        ['antivirus',     '6',  '240',  'yes'],
      ],
    },
    choices: ['system', 'browser (12 tabs)', 'music player', 'antivirus'],
    correctIndex: 1,
  },
  // ── interpret / JKI ──────────────────────────────────────────────────────────
  {
    kind: 'diagram_label', id: 'diagram_k8_jki_topology', conceptId: 'k8_networks_communication', strand: 'JKI',
    difficulty: 0.52, title: 'Label the home network',
    prompt: 'Drag the right label onto each part of this home network path.',
    diagram: 'network',
    slots: [
      { id: 's1', x: 60,  y: 70, answer: 'Device' },
      { id: 's2', x: 220, y: 70, answer: 'Router' },
      { id: 's3', x: 380, y: 70, answer: 'Internet' },
      { id: 's4', x: 540, y: 70, answer: 'Server' },
    ],
    bank: ['Router', 'Server', 'Device', 'Internet'],
  },
]

// Stable, demo-friendly ordering so each "next task" cycles to a different KIND.
export const DEMO_KIND_ORDER: TaskKind[] = [
  'mcq', 'trace', 'parsons', 'code_write', 'block_program',
  'case_study', 'data_interpretation', 'diagram_label',
  'video_question', 'audio_listen',
]

// ─── Lookups ────────────────────────────────────────────────────────────────────
export function taskKindMeta(kind: TaskKind): TaskKindMeta {
  return TASK_KIND_META[kind]
}

/** Cycle the pool by seed so successive tasks show different formats. */
export function pickDemoTask(seed?: number): DemoTask {
  if (seed == null) return DEMO_TASK_POOL[0]
  const idx = Math.abs(Math.floor(seed)) % DEMO_TASK_POOL.length
  return DEMO_TASK_POOL[idx]
}

/** First pool task for a concept (used to enrich a live recommendation). */
export function demoTaskForConcept(conceptId: string): DemoTask | null {
  return DEMO_TASK_POOL.find(t => t.conceptId === conceptId) ?? null
}

/** Map the MAB's modality string to the closest task kind. */
export function kindForModality(rep: string | null): TaskKind {
  if (!rep) return 'mcq'
  const r = rep.toLowerCase()
  if (r.includes('video')) return 'video_question'
  if (r.includes('audio') || r.includes('listen')) return 'audio_listen'
  if (r.includes('trace')) return 'trace'
  if (r.includes('parsons') || r.includes('order')) return 'parsons'
  if (r.includes('code')) return 'code_write'
  if (r.includes('block') || r.includes('visual')) return 'block_program'
  if (r.includes('case') || r.includes('scenario')) return 'case_study'
  if (r.includes('data') || r.includes('table')) return 'data_interpretation'
  if (r.includes('diagram') || r.includes('label')) return 'diagram_label'
  if (r.includes('interactive') || r.includes('drag') || r.includes('sort')) return 'parsons'
  return 'mcq'
}
