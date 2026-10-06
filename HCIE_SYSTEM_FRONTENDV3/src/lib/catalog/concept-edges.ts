/**
 * Concept dependency edges — snapshot of the `concept_dependencies` Postgres
 * table (2026-07-04), filtered to the 30 catalog concepts. Mirrors the DB
 * exactly (same pattern as K12_CONCEPTS mirroring `k12_concepts`): regenerate
 * with `SELECT source_concept, target_concept, transfer_weight, dependency_type
 * FROM concept_dependencies` if the curriculum topology changes.
 */
import type { ConceptEdge } from './k12-catalog'

export const CONCEPT_EDGES: ConceptEdge[] = [
  { source: 'k2_algorithms', target: 'k12_algorithms', transferWeight: 0.6, dependencyType: 'advanced' },
  { source: 'k2_algorithms', target: 'k5_algorithms', transferWeight: 0.85, dependencyType: 'prerequisite' },
  { source: 'k2_algorithms', target: 'k8_algorithms', transferWeight: 0.7, dependencyType: 'advanced' },
  { source: 'k2_computing_systems_devices', target: 'k5_computing_systems_devices', transferWeight: 0.9, dependencyType: 'prerequisite' },
  { source: 'k2_computing_systems_devices', target: 'k8_computing_systems_devices', transferWeight: 0.8, dependencyType: 'advanced' },
  { source: 'k2_control', target: 'k12_control', transferWeight: 0.6, dependencyType: 'advanced' },
  { source: 'k2_control', target: 'k5_control', transferWeight: 0.8, dependencyType: 'prerequisite' },
  { source: 'k2_control', target: 'k8_control', transferWeight: 0.7, dependencyType: 'advanced' },
  { source: 'k2_culture', target: 'k5_culture', transferWeight: 0.8, dependencyType: 'related' },
  { source: 'k2_culture', target: 'k8_culture', transferWeight: 0.7, dependencyType: 'advanced' },
  { source: 'k2_data_collection', target: 'k5_data_collection', transferWeight: 0.9, dependencyType: 'prerequisite' },
  { source: 'k2_data_collection', target: 'k8_data_collection', transferWeight: 0.8, dependencyType: 'advanced' },
  { source: 'k2_modularity', target: 'k5_modularity', transferWeight: 0.7, dependencyType: 'related' },
  { source: 'k2_modularity', target: 'k8_modularity', transferWeight: 0.6, dependencyType: 'advanced' },
  { source: 'k2_networks_communication', target: 'k5_networks_communication', transferWeight: 0.9, dependencyType: 'prerequisite' },
  { source: 'k2_networks_communication', target: 'k8_networks_communication', transferWeight: 0.8, dependencyType: 'advanced' },
  { source: 'k2_program_development', target: 'k5_program_development', transferWeight: 0.8, dependencyType: 'prerequisite' },
  { source: 'k2_program_development', target: 'k8_program_development', transferWeight: 0.7, dependencyType: 'advanced' },
  { source: 'k2_variables', target: 'k5_variables', transferWeight: 0.8, dependencyType: 'prerequisite' },
  { source: 'k2_variables', target: 'k8_variables', transferWeight: 0.7, dependencyType: 'advanced' },
]
