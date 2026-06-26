/**
 * Documentation Page
 * 
 * Comprehensive showcase of all components, pages, and files in the frontend.
 * Displays what each file does and how they're organized.
 */

'use client'

import { useState } from 'react'
import { useT } from '@/contexts/language_context'

interface DocItem {
  name: string
  description: string
  path: string
  type: 'component' | 'page' | 'lib' | 'config'
}

interface DocSection {
  title: string
  description: string
  items: DocItem[]
}

export default function DocumentationPage() {
  const t = useT()
  const [selectedSection, setSelectedSection] = useState<string>('components')

  const sections: DocSection[] = [
    {
      title: 'Components',
      description: 'UI components organized by feature area',
      items: [
        {
          name: 'Admin Components',
          description: 'Administrative interface for managing experiments, users, and system settings',
          path: '/src/components/admin',
          type: 'component'
        },
        {
          name: 'Dashboard Components',
          description: 'Main user-facing dashboard for learning, progress, and account management',
          path: '/src/components/dashboard',
          type: 'component'
        },
        {
          name: 'Learning Components',
          description: 'Learning-specific components for tasks and concept details',
          path: '/src/components/learning',
          type: 'component'
        },
        {
          name: 'Visualizations',
          description: 'Interactive algorithm visualizations (arrays, trees, graphs, sorting, etc.)',
          path: '/src/components/visualizations',
          type: 'component'
        },
        {
          name: 'Execution',
          description: 'Code execution engine and step-by-step visualization',
          path: '/src/components/execution',
          type: 'component'
        },
        {
          name: 'Research',
          description: 'Research dashboard components for data analysis and visualization',
          path: '/src/components/research',
          type: 'component'
        },
        {
          name: 'Shared',
          description: 'Reusable UI components (charts, cards, wizards, editors, etc.)',
          path: '/src/components/shared',
          type: 'component'
        },
        {
          name: 'UI',
          description: 'Base UI library components',
          path: '/src/components/ui',
          type: 'component'
        },
        {
          name: 'Providers',
          description: 'React context providers for global state',
          path: '/src/components/providers',
          type: 'component'
        }
      ]
    },
    {
      title: 'Pages',
      description: 'Application pages and routes',
      items: [
        {
          name: 'Home',
          description: 'Landing page with overview and quick access',
          path: '/src/app/page.tsx',
          type: 'page'
        },
        {
          name: 'Dashboard',
          description: 'Main user dashboard with learning overview',
          path: '/src/app/dashboard/page.tsx',
          type: 'page'
        },
        {
          name: 'Learning',
          description: 'Learning interface for tasks and feedback',
          path: '/src/app/learning/page.tsx',
          type: 'page'
        },
        {
          name: 'Progress',
          description: 'Detailed learning progress and analytics',
          path: '/src/app/progress/page.tsx',
          type: 'page'
        },
        {
          name: 'Profile',
          description: 'User profile and account management',
          path: '/src/app/profile/page.tsx',
          type: 'page'
        },
        {
          name: 'Settings',
          description: 'User preferences and configuration',
          path: '/src/app/settings/page.tsx',
          type: 'page'
        },
        {
          name: 'Tasks',
          description: 'Task history and submission tracking',
          path: '/src/app/tasks/page.tsx',
          type: 'page'
        },
        {
          name: 'Concepts',
          description: 'Detailed concept view with mastery progress',
          path: '/src/app/concepts/[id]/page.tsx',
          type: 'page'
        },
        {
          name: 'Visualizations',
          description: 'Algorithm visualization showcase',
          path: '/src/app/visualizations/page.tsx',
          type: 'page'
        },
        {
          name: 'System Status',
          description: 'System health and performance monitoring',
          path: '/src/app/system-status/page.tsx',
          type: 'page'
        },
        {
          name: 'Login',
          description: 'Authentication page',
          path: '/src/app/login/page.tsx',
          type: 'page'
        },
        {
          name: 'Admin',
          description: 'Administrative dashboard',
          path: '/src/app/admin/page.tsx',
          type: 'page'
        }
      ]
    },
    {
      title: 'Core Library',
      description: 'Business logic and interfaces',
      items: [
        {
          name: 'Interfaces',
          description: 'Type definitions and interfaces for core domain objects',
          path: '/src/lib/core/interfaces',
          type: 'lib'
        },
        {
          name: 'Services',
          description: 'Service interfaces for learning, auth, dashboard, experiments, WebSocket',
          path: '/src/lib/core/services',
          type: 'lib'
        },
        {
          name: 'Validators',
          description: 'Input validation logic for all domains',
          path: '/src/lib/core/validators',
          type: 'lib'
        },
        {
          name: 'Mappers',
          description: 'Data transformation between API and domain models',
          path: '/src/lib/core/mappers',
          type: 'lib'
        },
        {
          name: 'Factories',
          description: 'Service factory for dependency injection',
          path: '/src/lib/core/factories',
          type: 'lib'
        }
      ]
    },
    {
      title: 'Application Library',
      description: 'Application-specific logic and initialization',
      items: [
        {
          name: 'Services',
          description: 'Service initialization and container management',
          path: '/src/lib/application/services',
          type: 'lib'
        },
        {
          name: 'Contexts',
          description: 'React context providers (auth, config, services)',
          path: '/src/lib/application/contexts',
          type: 'lib'
        },
        {
          name: 'Bootstrap',
          description: 'Application bootstrap and initialization',
          path: '/src/lib/application/bootstrap',
          type: 'lib'
        }
      ]
    },
    {
      title: 'Configuration',
      description: 'Application configuration and settings',
      items: [
        {
          name: 'Config',
          description: 'Central configuration management with environment-specific settings',
          path: '/src/config/index.ts',
          type: 'config'
        }
      ]
    },
    {
      title: 'Contexts',
      description: 'React context providers for global state',
      items: [
        {
          name: 'Service Context',
          description: 'Provides initialized services to the application',
          path: '/src/contexts/service_context.tsx',
          type: 'lib'
        },
        {
          name: 'Auth Context',
          description: 'Manages authentication state and user session',
          path: '/src/contexts/auth_context.tsx',
          type: 'lib'
        },
        {
          name: 'Config Context',
          description: 'Provides application configuration',
          path: '/src/contexts/config_context.tsx',
          type: 'lib'
        }
      ]
    }
  ]

  const componentDetails: Record<string, string[]> = {
    'admin': [
      'AdminHome - Main admin dashboard with system overview and quick stats',
      'ExperimentsScreen - Experiment management interface',
      'AnalyticsScreen - System analytics dashboard with charts and metrics',
      'UsersScreen - User management interface',
      'AdminSettingsScreen - Admin-specific settings and configuration',
      'AdminNavigation - Navigation sidebar for admin dashboard',
      'AdminDashboardLayout - Main layout wrapper for admin pages'
    ],
    'dashboard': [
      'HomeScreen - Landing screen with learning overview and recommendations',
      'LearningScreen - Main learning interface for tasks and feedback',
      'ProgressScreen - Detailed learning progress and analytics',
      'ProfileScreen - User profile and account management',
      'SettingsScreen - User preferences (theme, language, notifications)',
      'Navigation - Main navigation bar for user dashboard',
      'DashboardLayout - Main layout wrapper for user dashboard pages'
    ],
    'learning': [
      'ConceptDetail - Detailed view of a specific learning concept',
      'TaskHistory - Display of user task submission history'
    ],
    'visualizations': [
      'ArrayVisualizer - Visualize array operations with highlighting',
      'BinaryVisualizer - Display binary sequences with bit manipulation',
      'MatrixVisualizer - Show 2D matrices with cell operations',
      'LinkedListVisualizer - Demonstrate linked list structure',
      'TreeVisualizer - Visualize binary and general tree structures',
      'GraphVisualizer - Display directed/undirected graphs',
      'StringVisualizer - Show string manipulation operations',
      'SortingVisualizer - Interactive sorting algorithm visualization',
      'CodeSnippet - Display code with syntax highlighting',
      'CodeFlowVisualizer - Line-by-line code execution tracking'
    ],
    'shared': [
      'RealTimeChart - Real-time data visualization',
      'StatCard - Display metrics and statistics',
      'ProgressRing - Circular progress indicator',
      'ActivityFeed - Show recent activities',
      'ConceptProgress - Display concept mastery progress',
      'LearningPath - Visualize learning path',
      'DAGVisualization - Directed acyclic graph visualization',
      'MathDisplay - Render mathematical expressions',
      'MathInput - Mathematical expression input',
      'OnboardingWizard - Step-by-step onboarding flow',
      'HelpCenter - Help documentation viewer',
      'ConceptManager - Manage learning concepts',
      'ConceptEditor - Edit concept definitions',
      'TaskManager - Manage learning tasks',
      'DependencyVisualizer - Visualize concept dependencies',
      'TextVisualizer - Text content viewer',
      'AudioVisualizer - Audio content player',
      'VideoVisualizer - Video content player',
      'CodeVisualizer - Code editor with execution',
      'BlocklyEditor - Visual block-based programming',
      'ContentViewer - Unified content viewer for all types'
    ]
  }

  const libDetails: Record<string, string[]> = {
    'interfaces': [
      'learning_interface.ts - ILearningService, ILearningMapper, LearningState, Task, TaskSubmission, SubmissionResult, Recommendation',
      'auth_interface.ts - IAuthService, IAuthMapper, User, AuthResponse, LoginCredentials, RegistrationData, PermissionCheck',
      'dashboard_interface.ts - IDashboardService, IDashboardMapper, UserDashboardData, AnalyticsQueryParams, AnalyticsData',
      'experiment_interface.ts - IExperimentService, IExperimentMapper, ExperimentConfig, ExperimentListResponse, GeneratedFigure',
      'state_interface.ts - IStateService, IStateMapper, SystemState, HealthCheck, PerformanceMetrics',
      'websocket_interface.ts - IWebSocketService, IWebSocketMapper, WebSocketConfig, WebSocketMessage, ConnectionEvent'
    ],
    'services': [
      'learning_service.ts - Learning service implementation for tasks, recommendations, and progress tracking',
      'auth_service.ts - Authentication service for login, logout, and user management',
      'dashboard_service.ts - Dashboard service for analytics and user data aggregation',
      'experiment_service.ts - Experiment service for running and managing experiments',
      'websocket_service.ts - WebSocket service for real-time communication'
    ],
    'validators': [
      'learning_validator.ts - Validates learning-related data (tasks, submissions, recommendations)',
      'auth_validator.ts - Validates authentication credentials and user data',
      'dashboard_validator.ts - Validates dashboard query parameters and analytics requests',
      'experiment_validator.ts - Validates experiment configurations and parameters',
      'websocket_validator.ts - Validates WebSocket messages and connection data'
    ],
    'mappers': [
      'learning_mapper.ts - Maps API responses to learning domain models and vice versa',
      'auth_mapper.ts - Maps API responses to authentication domain models',
      'dashboard_mapper.ts - Maps API responses to dashboard domain models',
      'experiment_mapper.ts - Maps API responses to experiment domain models',
      'websocket_mapper.ts - Maps WebSocket messages to domain models'
    ],
    'factories': [
      'service_factory.ts - Central factory for creating service instances with dependency injection'
    ],
    'service-initialization': [
      'service_initialization.ts - Initializes all services and manages the service container'
    ],
    'contexts': [
      'service_context.tsx - React context provider for initialized services',
      'auth_context.tsx - React context provider for authentication state',
      'config_context.tsx - React context provider for application configuration'
    ],
    'bootstrap': [
      'app_bootstrap.tsx - Application bootstrap component that wraps all providers'
    ]
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">{t('docs.title')}</h1>
          <p className="text-gray-600 mt-1">{t('docs.eyebrow')}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Navigation Tabs */}
        <div className="flex gap-2 mb-8 border-b border-gray-200">
          {sections.map(section => (
            <button
              key={section.title}
              onClick={() => setSelectedSection(section.title.toLowerCase())}
              className={`px-4 py-3 font-medium transition-colors ${
                selectedSection === section.title.toLowerCase()
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {section.title}
            </button>
          ))}
        </div>

        {/* Content */}
        {sections.map(section => (
          selectedSection === section.title.toLowerCase() && (
            <div key={section.title} className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{section.title}</h2>
                <p className="text-gray-600 mb-6">{section.description}</p>
                
                <div className="space-y-4">
                  {section.items.map(item => (
                    <div
                      key={item.name}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900">{item.name}</h3>
                          <p className="text-gray-600 mt-1">{item.description}</p>
                          <code className="inline-block mt-2 px-3 py-1 bg-gray-100 rounded text-sm text-gray-700">
                            {item.path}
                          </code>
                        </div>
                        <span className={`ml-4 px-3 py-1 rounded-full text-sm font-medium ${
                          item.type === 'component' ? 'bg-blue-100 text-blue-700' :
                          item.type === 'page' ? 'bg-green-100 text-green-700' :
                          item.type === 'lib' ? 'bg-purple-100 text-purple-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {item.type}
                        </span>
                      </div>

                      {/* Show detailed components for certain sections */}
                      {item.path.includes('/components/') && item.name.toLowerCase().includes('components') && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">Components in this directory:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {Object.entries(componentDetails).map(([key, components]) => {
                              if (item.name.toLowerCase().includes(key)) {
                                return components.map(comp => (
                                  <div key={comp} className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                                    {comp}
                                  </div>
                                ))
                              }
                              return null
                            })}
                          </div>
                        </div>
                      )}

                      {/* Show detailed lib files for lib sections */}
                      {item.path.includes('/lib/') && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <h4 className="text-sm font-semibold text-gray-700 mb-2">Files in this directory:</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {Object.entries(libDetails).map(([key, files]) => {
                              const dirName = item.path.split('/').pop()?.toLowerCase() || ''
                              if (dirName === key || dirName === key.replace('-', '')) {
                                return files.map(file => (
                                  <div key={file} className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                                    {file}
                                  </div>
                                ))
                              }
                              return null
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        ))}

        {/* Quick Reference */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Quick Reference</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <strong className="text-blue-800">Components:</strong> UI building blocks organized by feature
            </div>
            <div>
              <strong className="text-blue-800">Pages:</strong> Application routes and screens
            </div>
            <div>
              <strong className="text-blue-800">Lib/Core:</strong> Business logic and interfaces
            </div>
            <div>
              <strong className="text-blue-800">Lib/Application:</strong> App-specific logic
            </div>
            <div>
              <strong className="text-blue-800">Config:</strong> Configuration management
            </div>
            <div>
              <strong className="text-blue-800">Contexts:</strong> Global state providers
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
