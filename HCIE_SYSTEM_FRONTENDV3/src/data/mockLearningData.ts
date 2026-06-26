/**
 * Mock Learning Data
 * 
 * Sample data for multi-method learning system aligned with backend schema
 */

import { Concept, LearningMethod } from '@/types/learning'

export const mockConcepts: Concept[] = [
  {
    id: 'k2_algorithms',
    gradeBand: 'K-2',
    conceptArea: 'Algorithms',
    cognitiveLevel: 1,
    difficulty: 0.2,
    description: 'k2_algorithms',
    learningObjectives: ['Understand', 'Apply', 'Analyze'],
    masteryLevel: 85,
    masteryProbability: 0.85,
    confidenceInterval: { lower: 0.78, upper: 0.92 },
    prerequisites: [],
    dependsOn: ['k5_algorithms'],
    tasks: [
      {
        id: 'k2_algorithms_text_v1',
        conceptId: 'k2_algorithms',
        name: 'Identify Algorithms',
        description: 'Find algorithms in daily life',
        method: 'text',
        order: 1,
        content: {
          text: {
            content: 'An algorithm is a step-by-step set of instructions to solve a problem.',
            examples: [
              'Recipe for cooking',
              'Directions to a location',
              'Morning routine'
            ],
            exercises: [
              {
                id: 'ex-001',
                question: 'Which is an algorithm?',
                type: 'multiple-choice',
                options: ['A recipe', 'A feeling', 'A color', 'A sound'],
                correctAnswer: 'A recipe',
                explanation: 'A recipe has step-by-step instructions'
              }
            ]
          }
        },
        difficulty: 1,
        estimatedTime: 5,
        completed: true,
        irtDifficulty: -1.2,
        irtDiscrimination: 1.5,
        responseTime: 45,
        attempts: 1
      },
      {
        id: 'k2_algorithms_code_v1',
        conceptId: 'k2_algorithms',
        name: 'Simple Algorithm',
        description: 'Create step-by-step algorithm',
        method: 'code',
        order: 2,
        content: {
          code: {
            starterCode: `// Write steps to brush teeth
function brushTeeth() {
  // Your code here
}`,
            solution: `function brushTeeth() {
  putToothpasteOnBrush();
  brushAllTeeth(30);
  rinseMouth();
  cleanBrush();
}`,
            language: 'javascript',
            tests: [
              {
                id: 'test-001',
                input: 'brushTeeth()',
                expectedOutput: 'Teeth brushed',
                isHidden: false
              }
            ],
            hints: ['Think about the order', 'Include rinsing']
          }
        },
        difficulty: 2,
        estimatedTime: 10,
        completed: true,
        irtDifficulty: -0.8,
        irtDiscrimination: 1.8,
        responseTime: 120,
        attempts: 2
      },
      {
        id: 'k2_algorithms_interactive_v1',
        conceptId: 'k2_algorithms',
        name: 'Interactive Practice',
        description: 'Arrange steps in correct order',
        method: 'interactive',
        order: 3,
        content: {
          interactive: {
            type: 'visualization',
            config: {
              activity: 'sort-steps',
              steps: ['Get toothbrush', 'Put toothpaste', 'Brush teeth', 'Rinse'],
              correctOrder: [1, 2, 3, 4]
            }
          }
        },
        difficulty: 2,
        estimatedTime: 8,
        completed: false,
        irtDifficulty: -0.5,
        irtDiscrimination: 1.6
      }
    ],
    estimatedTime: 23,
    banditScore: 0.15,
    recommended: false,
    spacedRepetition: {
      nextReview: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      interval: 7,
      easeFactor: 2.5
    },
    learningCurve: {
      timestamps: [Date.now() - 30 * 24 * 60 * 60 * 1000, Date.now() - 20 * 24 * 60 * 60 * 1000, Date.now() - 10 * 24 * 60 * 60 * 1000, Date.now()],
      masteryValues: [0.3, 0.5, 0.7, 0.85]
    }
  },
  {
    id: 'k5_algorithms',
    gradeBand: 'K-5',
    conceptArea: 'Algorithms',
    cognitiveLevel: 2,
    difficulty: 0.4,
    description: 'k5_algorithms',
    learningObjectives: ['Understand', 'Apply', 'Analyze'],
    masteryLevel: 45,
    masteryProbability: 0.45,
    confidenceInterval: { lower: 0.35, upper: 0.55 },
    prerequisites: ['k2_algorithms'],
    dependsOn: ['k8_variables'],
    tasks: [
      {
        id: 'k5_algorithms_text_v1',
        conceptId: 'k5_algorithms',
        name: 'Design Algorithm',
        description: 'Create algorithm for problem',
        method: 'text',
        order: 1,
        content: {
          text: {
            content: 'Design an algorithm to find the largest number in a list.',
            examples: [
              'Input: [3, 7, 2, 9, 1]',
              'Output: 9'
            ],
            exercises: [
              {
                id: 'ex-002',
                question: 'What is the first step in finding the largest number?',
                type: 'multiple-choice',
                options: ['Start with first number', 'Sort the list', 'Count the numbers', 'Add them all'],
                correctAnswer: 'Start with first number',
                explanation: 'We need a starting point for comparison'
              }
            ]
          }
        },
        difficulty: 3,
        estimatedTime: 8,
        completed: false,
        irtDifficulty: 0.2,
        irtDiscrimination: 1.4
      },
      {
        id: 'k5_algorithms_code_v1',
        conceptId: 'k5_algorithms',
        name: 'Code Implementation',
        description: 'Write code to find largest number',
        method: 'code',
        order: 2,
        content: {
          code: {
            starterCode: `function findLargest(numbers) {
  // Your code here
  return largest;
}`,
            solution: `function findLargest(numbers) {
  let largest = numbers[0];
  for (let i = 1; i < numbers.length; i++) {
    if (numbers[i] > largest) {
      largest = numbers[i];
    }
  }
  return largest;
}`,
            language: 'javascript',
            tests: [
              {
                id: 'test-002',
                input: 'findLargest([3, 7, 2, 9, 1])',
                expectedOutput: '9',
                isHidden: false
              }
            ],
            hints: ['Use a loop', 'Compare each number']
          }
        },
        difficulty: 4,
        estimatedTime: 15,
        completed: false,
        irtDifficulty: 0.5,
        irtDiscrimination: 1.6
      },
      {
        id: 'k5_algorithms_video_v1',
        conceptId: 'k5_algorithms',
        name: 'Video Tutorial',
        description: 'Watch step-by-step algorithm design',
        method: 'video',
        order: 3,
        content: {
          video: {
            url: 'https://example.com/videos/k5-algorithms.mp4',
            duration: 600,
            transcript: 'In this video, we will learn how to design algorithms...'
          }
        },
        difficulty: 3,
        estimatedTime: 10,
        completed: false,
        irtDifficulty: 0.1,
        irtDiscrimination: 1.3
      }
    ],
    estimatedTime: 33,
    banditScore: 0.85,
    recommended: true,
    spacedRepetition: {
      nextReview: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
      interval: 1,
      easeFactor: 2.0
    },
    learningCurve: {
      timestamps: [Date.now() - 10 * 24 * 60 * 60 * 1000, Date.now()],
      masteryValues: [0.3, 0.45]
    }
  },
  {
    id: 'k8_variables',
    gradeBand: 'K-8',
    conceptArea: 'Variables',
    cognitiveLevel: 3,
    difficulty: 0.6,
    description: 'k8_variables',
    learningObjectives: ['Understand', 'Apply', 'Analyze'],
    masteryLevel: 0,
    masteryProbability: 0.0,
    confidenceInterval: { lower: 0.0, upper: 0.1 },
    prerequisites: ['k5_algorithms'],
    dependsOn: ['k12_control_structures'],
    tasks: [
      {
        id: 'k8_variables_text_v1',
        conceptId: 'k8_variables',
        name: 'Variable Basics',
        description: 'Understand variable concepts',
        method: 'text',
        order: 1,
        content: {
          text: {
            content: 'Variables are containers for storing data values.',
            examples: [
              'let x = 5;',
              'let name = "Alice";',
              'let isActive = true;'
            ],
            exercises: [
              {
                id: 'ex-003',
                question: 'What does a variable store?',
                type: 'multiple-choice',
                options: ['Data values', 'Functions', 'Classes', 'Modules'],
                correctAnswer: 'Data values',
                explanation: 'Variables store data values'
              }
            ]
          }
        },
        difficulty: 4,
        estimatedTime: 10,
        completed: false,
        irtDifficulty: 0.8,
        irtDiscrimination: 1.5
      },
      {
        id: 'k8_variables_code_v1',
        conceptId: 'k8_variables',
        name: 'Variable Operations',
        description: 'Practice with variable operations',
        method: 'code',
        order: 2,
        content: {
          code: {
            starterCode: `let a = 10;
let b = 5;
// Calculate sum, difference, product, quotient
`,
            solution: `let a = 10;
let b = 5;
let sum = a + b;
let diff = a - b;
let prod = a * b;
let quot = a / b;
`,
            language: 'javascript',
            tests: [
              {
                id: 'test-003',
                input: 'sum',
                expectedOutput: '15',
                isHidden: false
              }
            ],
            hints: ['Use + for sum', 'Use - for difference']
          }
        },
        difficulty: 5,
        estimatedTime: 12,
        completed: false,
        irtDifficulty: 1.0,
        irtDiscrimination: 1.7
      },
      {
        id: 'k8_variables_multiple_choice_v1',
        conceptId: 'k8_variables',
        name: 'Variable Quiz',
        description: 'Test variable knowledge',
        method: 'multiple_choice',
        order: 3,
        content: {
          quiz: {
            questions: [
              {
                id: 'q-001',
                question: 'Which keyword declares a variable in JavaScript?',
                type: 'multiple-choice',
                options: ['var', 'let', 'const', 'All of the above'],
                correctAnswer: 'All of the above',
                explanation: 'All three keywords can declare variables',
                points: 10
              },
              {
                id: 'q-002',
                question: 'Variables can store numbers only.',
                type: 'true-false',
                correctAnswer: 'false',
                explanation: 'Variables can store numbers, strings, booleans, etc.',
                points: 10
              }
            ],
            passingScore: 70,
            timeLimit: 300
          }
        },
        difficulty: 4,
        estimatedTime: 8,
        completed: false,
        irtDifficulty: 0.6,
        irtDiscrimination: 1.4
      }
    ],
    estimatedTime: 30,
    banditScore: 0.65,
    recommended: false,
    learningCurve: {
      timestamps: [Date.now()],
      masteryValues: [0.0]
    }
  },
  {
    id: 'k12_control_structures',
    gradeBand: 'K-12',
    conceptArea: 'Control Structures',
    cognitiveLevel: 4,
    difficulty: 0.8,
    description: 'k12_control_structures',
    learningObjectives: ['Understand', 'Apply', 'Analyze'],
    masteryLevel: 0,
    masteryProbability: 0.0,
    confidenceInterval: { lower: 0.0, upper: 0.1 },
    prerequisites: ['k8_variables'],
    dependsOn: [],
    tasks: [
      {
        id: 'k12_control_text_v1',
        conceptId: 'k12_control_structures',
        name: 'Control Flow',
        description: 'Understand if-else and loops',
        method: 'text',
        order: 1,
        content: {
          text: {
            content: 'Control structures determine the flow of program execution.',
            examples: [
              'if (condition) { } else { }',
              'for (let i = 0; i < n; i++) { }',
              'while (condition) { }'
            ],
            exercises: [
              {
                id: 'ex-004',
                question: 'Which control structure repeats code?',
                type: 'multiple-choice',
                options: ['if-else', 'switch', 'loops', 'try-catch'],
                correctAnswer: 'loops',
                explanation: 'Loops repeat code blocks'
              }
            ]
          }
        },
        difficulty: 6,
        estimatedTime: 12,
        completed: false,
        irtDifficulty: 1.2,
        irtDiscrimination: 1.6
      },
      {
        id: 'k12_control_code_v1',
        conceptId: 'k12_control_structures',
        name: 'Advanced Control',
        description: 'Implement complex control structures',
        method: 'code',
        order: 2,
        content: {
          code: {
            starterCode: `function findPrimes(n) {
  // Find all primes up to n
  // Use loops and conditionals
}`,
            solution: `function findPrimes(n) {
  const primes = [];
  for (let i = 2; i <= n; i++) {
    let isPrime = true;
    for (let j = 2; j <= Math.sqrt(i); j++) {
      if (i % j === 0) {
        isPrime = false;
        break;
      }
    }
    if (isPrime) {
      primes.push(i);
    }
  }
  return primes;
}`,
            language: 'javascript',
            tests: [
              {
                id: 'test-004',
                input: 'findPrimes(10)',
                expectedOutput: '[2, 3, 5, 7]',
                isHidden: false
              }
            ],
            hints: ['Use nested loops', 'Check divisibility']
          }
        },
        difficulty: 7,
        estimatedTime: 20,
        completed: false,
        irtDifficulty: 1.5,
        irtDiscrimination: 1.8
      },
      {
        id: 'k12_control_interactive_v1',
        conceptId: 'k12_control_structures',
        name: 'Flow Visualization',
        description: 'Visualize control flow',
        method: 'interactive',
        order: 3,
        content: {
          interactive: {
            type: 'visualization',
            config: {
              activity: 'flowchart-builder',
              elements: ['start', 'condition', 'loop', 'end'],
              connections: []
            }
          }
        },
        difficulty: 6,
        estimatedTime: 15,
        completed: false,
        irtDifficulty: 1.3,
        irtDiscrimination: 1.5
      }
    ],
    estimatedTime: 47,
    banditScore: 0.45,
    recommended: false,
    learningCurve: {
      timestamps: [Date.now()],
      masteryValues: [0.0]
    }
  }
]

export const learningMethodConfig: Record<LearningMethod, { icon: string; label: string; description: string }> = {
  text: {
    icon: '📄',
    label: 'Text',
    description: 'Read and learn through written content'
  },
  video: {
    icon: '🎥',
    label: 'Video',
    description: 'Watch video tutorials and demonstrations'
  },
  code: {
    icon: '💻',
    label: 'Code',
    description: 'Write and practice code implementations'
  },
  multiple_choice: {
    icon: '❓',
    label: 'Multiple Choice',
    description: 'Test your knowledge with quizzes'
  },
  interactive: {
    icon: '🎯',
    label: 'Interactive',
    description: 'Explore concepts through interactive simulations'
  }
}
